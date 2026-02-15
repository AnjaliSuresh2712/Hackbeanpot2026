"""
Question generation module using Snowflake Cortex LLM
"""
from typing import List, Dict
import snowflake.connector
import json
import re

# Health impact configuration based on difficulty
HEALTH_IMPACTS = {
    "easy": {"correct": 5, "wrong": -2},
    "medium": {"correct": 10, "wrong": -5},
    "hard": {"correct": 20, "wrong": -10}
}

# Letter to 0-based index for frontend
LETTER_TO_INDEX = {"A": 0, "B": 1, "C": 2, "D": 3}

# Skip this many chars from start of PDF to avoid course title / header / date
CONTENT_START_SKIP = 400


def _content_only_text(text: str) -> str:
    """
    Strip likely header/title from PDF (first line often has course code, title, date).
    Use the rest so questions are about actual lecture content, not "CS 3000 Jan 30".
    """
    if not text or len(text) < CONTENT_START_SKIP:
        return (text or "").strip()
    # Skip first N chars; try to start after a newline so we don't cut a word in half
    start = CONTENT_START_SKIP
    newline = text.find("\n", CONTENT_START_SKIP // 2)
    if 0 <= newline < CONTENT_START_SKIP + 200:
        start = newline + 1
    return text[start:].strip() or text.strip()


def _chunk_text(text: str, max_chunk_len: int = 8000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks so we can use different content per batch for variety."""
    if len(text) <= max_chunk_len:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chunk_len
        chunk = text[start:end]
        # Try to break at sentence boundary
        last_period = chunk.rfind(".")
        if last_period > max_chunk_len // 2:
            chunk = chunk[: last_period + 1]
            end = start + len(chunk)
        chunks.append(chunk)
        start = end - overlap if end < len(text) else len(text)
    return chunks


def _extract_response_text(result_value: str) -> str:
    """Handle both raw string and Snowflake COMPLETE options response (JSON with choices[].messages)."""
    if not result_value:
        return ""
    stripped = result_value.strip()
    # If response is JSON (when using options like temperature), extract the message
    if stripped.startswith("{"):
        try:
            data = json.loads(stripped)
            choices = data.get("choices") or []
            if choices and isinstance(choices[0], dict) and "messages" in choices[0]:
                return (choices[0].get("messages") or "").strip()
            if choices and isinstance(choices[0], dict) and "message" in choices[0]:
                msg = choices[0]["message"]
                return (msg.get("content", msg) if isinstance(msg, dict) else str(msg)).strip()
        except json.JSONDecodeError:
            pass
    return stripped


def generate_questions(
    pdf_text: str,
    num_easy: int,
    num_medium: int,
    num_hard: int,
    snowflake_conn: snowflake.connector.SnowflakeConnection,
) -> List[Dict]:
    """
    Generate questions from PDF text using Snowflake Cortex.
    Uses different text chunks per difficulty for variety; enforces content-specific
    questions, unique options, and a single correct answer.
    """
    questions = []
    cursor = snowflake_conn.cursor()
    full_text = (pdf_text or "").strip()
    if not full_text:
        return []

    # Use body content only so we don't build questions from course title/header (e.g. "CS 3000 Jan 30")
    content_text = _content_only_text(full_text)
    if len(content_text) < 200:
        content_text = full_text
    chunks = _chunk_text(content_text, max_chunk_len=8000, overlap=300)

    try:
        for difficulty, count in [("easy", num_easy), ("medium", num_medium), ("hard", num_hard)]:
            if count <= 0:
                continue

            # Use a different chunk for each difficulty so questions aren't all from the same slice
            chunk_index = (["easy", "medium", "hard"].index(difficulty)) % len(chunks)
            content = chunks[chunk_index]

            system_prompt = (
                "You are an expert educational question writer. You generate multiple choice questions "
                "in valid JSON only. Base questions ONLY on the actual body content (definitions, steps, facts, examples). "
                "Ignore document titles, course codes, and dates. Each question must ask about a SPECIFIC fact, term, or idea from the text. "
                "Wrong answers must be plausible distractors (similar-sounding or related but wrong). "
                "VARY which option is correct: use A, B, C, and D across questions, not always A. "
                "Exactly one option per question is correct; correct_answer is that option's letter."
            ).replace("'", "''")

            user_prompt = f"""The following is BODY CONTENT from a lecture or textbook (titles/headers removed). Create {count} {difficulty}-level multiple choice questions that help a student learn THIS material.

Content:
{content}

RULES:
- Generate exactly {count} questions. Each question must ask about a SPECIFIC concept, definition, step, or fact stated in the content (e.g. "What is X?", "According to the text, how does Y work?", "Which of the following is true about Z?").
- Do NOT ask vague questions like "what best describes the material" or "what is the main topic". Ask about concrete things: terms, numbers, steps, causes, examples.
- Each question has exactly 4 options. The 3 wrong options must be plausible but incorrect (e.g. other terms from the text, common wrong answers). All four option texts must be DIFFERENT.
- VARY the correct answer: across your {count} questions, use different letters (A, B, C, D) as correct_answer, not always A.
- Easy: recall definitions, key terms, explicit facts. Medium: apply a concept, compare, explain. Hard: synthesize, infer, or evaluate.

Output format — return ONLY a JSON array, no markdown:
[
  {{ "question": "Specific question about a concrete fact or term?", "options": ["Option A", "Option B", "Option C", "Option D"], "correct_answer": "B" }}
]

Return ONLY the JSON array.""".replace(
                "'", "''"
            )

            # Use COMPLETE with temperature for variety; options format returns JSON so we parse choices[0].messages
            query = f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'llama3.1-8b',
                [
                    {{'role': 'system', 'content': '{system_prompt}'}},
                    {{'role': 'user', 'content': '{user_prompt}'}}
                ],
                {{ 'temperature': 0.7, 'max_tokens': 4096 }}
            ) AS response
            """
            cursor.execute(query)
            row = cursor.fetchone()
            response_text = _extract_response_text(row[0]) if row and row[0] else ""

            try:
                json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
                json_str = json_match.group(0) if json_match else response_text
                question_data = json.loads(json_str)
            except (json.JSONDecodeError, AttributeError) as e:
                raise ValueError(
                    f"LLM returned invalid JSON for {difficulty} questions: {e}. "
                    "Check Snowflake Cortex is enabled and the model returned valid JSON."
                ) from e

            if not isinstance(question_data, list):
                raise ValueError(
                    f"LLM did not return a JSON array for {difficulty}. "
                    "Check Snowflake Cortex response format."
                )

            impacts = HEALTH_IMPACTS[difficulty]
            n_before_difficulty = len(questions)
            for q in question_data:
                if not isinstance(q, dict) or "question" not in q or "options" not in q:
                    continue
                options = q.get("options")
                if not isinstance(options, list) or len(options) != 4:
                    continue
                # Normalize options (strings, unique)
                options = [str(o).strip() for o in options]
                if len(set(options)) < 4:
                    continue
                raw_correct = q.get("correct_answer")
                correct_answer = str(raw_correct).upper().strip() if raw_correct is not None else ""
                if correct_answer not in ("A", "B", "C", "D"):
                    if str(raw_correct).isdigit():
                        idx = int(raw_correct) - 1
                        if 0 <= idx < 4:
                            correct_answer = ["A", "B", "C", "D"][idx]
                    if correct_answer not in ("A", "B", "C", "D"):
                        continue
                correct_index = LETTER_TO_INDEX[correct_answer]
                questions.append({
                    "question": str(q.get("question", "")).strip() or "No question text.",
                    "difficulty": difficulty,
                    "options": options,
                    "correct_answer": correct_answer,
                    "correctIndex": correct_index,
                    "health_impact": {"correct": impacts["correct"], "wrong": impacts["wrong"]},
                })
            if len(questions) == n_before_difficulty:
                raise ValueError(
                    f"LLM returned no valid {difficulty} questions (need 4 unique options and correct_answer A-D). "
                    "Try again or check the model output."
                )

        if not questions:
            raise ValueError(
                "LLM produced no valid questions. Check Snowflake Cortex and that the model returns valid JSON with question, options (4 items), and correct_answer (A/B/C/D)."
            )
        return questions

    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Snowflake Cortex error: {e}") from e
    finally:
        cursor.close()

def create_fallback_question(difficulty: str, text: str) -> Dict:
    """Create a simple fallback question if LLM generation fails. Uses content from the text."""
    impacts = HEALTH_IMPACTS[difficulty]
    content = _content_only_text(text)
    sentences = [s.strip() for s in content.split(".") if len(s.strip()) > 30 and not _looks_like_code(s.strip())][2:8]
    if not sentences:
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 20][:4]
    focus = _clean_option_text(sentences[0], 80) if sentences else "The main idea is explained in the text."
    return {
        "question": "Which of the following is stated in the reading?",
        "difficulty": difficulty,
        "options": [
            focus,
            "This is not stated in the text.",
            "The text does not say this.",
            "This goes beyond what the material says.",
        ],
        "correct_answer": "A",
        "correctIndex": 0,
        "health_impact": {"correct": impacts["correct"], "wrong": impacts["wrong"]},
    }


def create_fallback_questions(text: str, num_easy: int, num_medium: int, num_hard: int) -> List[Dict]:
    """Create fallback questions if LLM generation completely fails."""
    return [
        create_fallback_question(difficulty, text)
        for difficulty, count in [("easy", num_easy), ("medium", num_medium), ("hard", num_hard)]
        for _ in range(count)
    ]

def _looks_like_code(s: str) -> bool:
    """Heuristic: sentence looks like code or pseudocode rather than prose."""
    if not s or len(s) < 10:
        return True
    # Common code patterns
    if re.search(r"←|:=|def\s+|function\s*\(|Merge\s*\(|len\s*\(", s, re.IGNORECASE):
        return True
    if re.search(r"^\s*\w+\s*\([^)]*\)\s*:", s):  # e.g. "Merge(L,R):"
        return True
    # Too many symbols
    sym = sum(1 for c in s if c in "()[]{}=<>")
    if sym >= 3 or (sym >= 2 and len(s) < 60):
        return True
    return False


def _sentences_from_content(text: str, min_len: int = 25, max_sentences: int = 30) -> List[str]:
    """Extract substantive prose sentences from body text (skip headers and code-like lines)."""
    content = _content_only_text(text)
    if len(content) < 100:
        content = text
    raw = [s.strip() for s in re.split(r"[.!?]\s+", content) if s.strip()]
    out = []
    for s in raw:
        if len(s) < min_len:
            continue
        if re.match(r"^[\d\s:/-]+$", s):
            continue
        if _looks_like_code(s):
            continue
        out.append(s.strip())
        if len(out) >= max_sentences:
            break
    # If we filtered too much, add back some longer fragments (still skip pure code)
    if len(out) < 5 and raw:
        for s in raw:
            if s in out or len(s) < min_len:
                continue
            if _looks_like_code(s):
                continue
            out.append(s.strip())
            if len(out) >= max_sentences:
                break
    return out


def _clean_option_text(sentence: str, max_len: int = 95) -> str:
    """Turn a sentence into a clean multiple-choice option (no code dump)."""
    s = sentence.strip()
    if len(s) <= max_len:
        return s
    # Prefer first clause or first sentence
    for sep in ". ", ", ":
        idx = s.find(sep, 20, max_len + 20)
        if idx > 30:
            return s[: idx + 1].strip()
    return s[: max_len - 1].strip() + "…"


def generate_questions_content_fallback(
    pdf_text: str,
    num_easy: int,
    num_medium: int,
    num_hard: int,
) -> List[Dict]:
    """
    Generate questions from PDF text without an LLM: uses real sentences from the
    document as correct answers and distractors. Correct answer varies (A/B/C/D).
    Used when Snowflake is not configured.
    """
    questions = []
    sentences = _sentences_from_content(pdf_text or "", min_len=30, max_sentences=40)
    if not sentences:
        # Last resort when we couldn't extract prose sentences
        stems = [
            "Which of these might the material cover?",
            "What kind of content does the reading likely include?",
            "Which is a plausible topic for this text?",
        ]
        for difficulty, count in [("easy", num_easy), ("medium", num_medium), ("hard", num_hard)]:
            impacts = HEALTH_IMPACTS[difficulty]
            for i in range(count):
                ci = i % 4
                opts = [
                    "A key concept or definition from the material",
                    "A supporting detail or example from the text",
                    "An application or procedure explained in the reading",
                    "A main idea or conclusion in the material",
                ]
                questions.append({
                    "question": stems[i % len(stems)],
                    "difficulty": difficulty,
                    "options": opts,
                    "correct_answer": ["A", "B", "C", "D"][ci],
                    "correctIndex": ci,
                    "health_impact": {"correct": impacts["correct"], "wrong": impacts["wrong"]},
                })
        return questions

    # Question stems so we don't repeat "According to the material..." every time
    question_stems = [
        "Which of the following is stated in the reading?",
        "What does the text say? Pick the option that appears in the material.",
        "The material explains or states one of the options below. Which one?",
        "Which statement is found in the text?",
        "One of these is directly stated or explained in the reading. Which?",
        "Which of these does the text support?",
        "The reading includes or implies one of these. Which option?",
        "Which of the following is correct according to the material?",
    ]

    per_difficulty = [("easy", num_easy), ("medium", num_medium), ("hard", num_hard)]
    sentence_idx = 0
    correct_position = 0
    generic_wrong = [
        "This is not stated or implied in the text.",
        "The text does not say this.",
        "This contradicts or goes beyond the material.",
    ]

    for difficulty, count in per_difficulty:
        impacts = HEALTH_IMPACTS[difficulty]
        for q_num in range(count):
            if sentence_idx >= len(sentences):
                sentence_idx = 0
            correct_sentence = sentences[sentence_idx]
            sentence_idx += 1
            correct_option = _clean_option_text(correct_sentence, max_len=95)
            wrong_options = []
            for j in range(1, 4):
                other_idx = (sentence_idx - 1 + j) % len(sentences)
                if sentences[other_idx] != correct_sentence:
                    other = _clean_option_text(sentences[other_idx], max_len=90)
                    if other not in wrong_options and other != correct_option:
                        wrong_options.append(other)
            while len(wrong_options) < 3:
                wrong_options.append(generic_wrong[len(wrong_options) % 3])
            wrong_options = wrong_options[:3]
            ci = correct_position % 4
            correct_position += 1
            opts = [""] * 4
            opts[ci] = correct_option
            w = 0
            for i in range(4):
                if opts[i] == "":
                    opts[i] = wrong_options[w]
                    w += 1

            stem_idx = (q_num + correct_position - 1) % len(question_stems)
            questions.append({
                "question": question_stems[stem_idx],
                "difficulty": difficulty,
                "options": opts,
                "correct_answer": ["A", "B", "C", "D"][ci],
                "correctIndex": ci,
                "health_impact": {"correct": impacts["correct"], "wrong": impacts["wrong"]},
            })

    return questions

