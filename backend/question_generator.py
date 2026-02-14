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

def generate_questions(
    pdf_text: str,
    num_easy: int,
    num_medium: int,
    num_hard: int,
    snowflake_conn: snowflake.connector.SnowflakeConnection
) -> List[Dict]:
    """
    Generate questions from PDF text using Snowflake Cortex.
    
    Args:
        pdf_text: The text extracted from the PDF
        num_easy: Number of easy questions to generate
        num_medium: Number of medium questions to generate
        num_hard: Number of hard questions to generate
        snowflake_conn: Snowflake connection object
        
    Returns:
        List of question dictionaries with difficulty, question, options, and correct_answer
    """
    questions = []
    cursor = snowflake_conn.cursor()
    
    try:
        # Truncate text if too long (Snowflake has limits)
        max_text_length = 10000  # Adjust based on your needs
        truncated_text = pdf_text[:max_text_length] if len(pdf_text) > max_text_length else pdf_text
        
        # Generate questions for each difficulty level
        for difficulty, count in [("easy", num_easy), ("medium", num_medium), ("hard", num_hard)]:
            if count <= 0:
                continue
            
            # Create prompt for question generation
            prompt = f"""Based on the following educational content, generate {count} {difficulty}-level multiple choice questions.

Content:
{truncated_text}

IMPORTANT REQUIREMENTS:
1. Each question MUST have exactly 4 answer options (A, B, C, D)
2. Only one option should be correct
3. The other 3 options should be plausible but incorrect
4. Questions should test understanding of the content, not just memorization

For each question, provide:
1. A clear, {difficulty}-level question
2. Exactly four answer options labeled A, B, C, D
3. The correct answer (must be "A", "B", "C", or "D")

Format your response as JSON array with this structure:
[
  {{
    "question": "Question text here?",
    "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
    "correct_answer": "A"
  }}
]

Generate exactly {count} questions. Make them {difficulty}-level appropriate:
- Easy: Basic recall, definitions, simple concepts, straightforward facts
- Medium: Application of concepts, analysis, moderate complexity, requires understanding
- Hard: Synthesis of multiple concepts, evaluation, complex reasoning, critical thinking

CRITICAL: Return ONLY the JSON array. No markdown, no code blocks, no explanations. Just the raw JSON array."""

            # Use Snowflake Cortex COMPLETE function
            # Escape single quotes in the prompt for SQL
            escaped_prompt = prompt.replace("'", "''")
            escaped_system = "You are an educational question generator. Generate multiple choice questions in valid JSON format only.".replace("'", "''")
            
            # Try different Snowflake Cortex function formats
            # Format 1: With messages array (most common)
            query = f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'llama-3.1-8b-instruct',
                [
                    {{'role': 'system', 'content': '{escaped_system}'}},
                    {{'role': 'user', 'content': '{escaped_prompt}'}}
                ]
            ) AS response
            """
            
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result and result[0]:
                response_text = result[0]
                
                # Parse JSON from response
                try:
                    # Extract JSON from response (in case there's extra text)
                    json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        question_data = json.loads(json_str)
                    else:
                        # Try parsing the whole response
                        question_data = json.loads(response_text)
                    
                    # Process each question
                    for q in question_data:
                        if isinstance(q, dict) and "question" in q and "options" in q and "correct_answer" in q:
                            # Validate question structure
                            options = q["options"]
                            correct_answer = str(q["correct_answer"]).upper().strip()
                            
                            # Ensure we have exactly 4 options
                            if not isinstance(options, list) or len(options) != 4:
                                print(f"Warning: Question has {len(options) if isinstance(options, list) else 0} options, expected 4. Skipping.")
                                continue
                            
                            # Validate correct answer is A, B, C, or D
                            if correct_answer not in ["A", "B", "C", "D"]:
                                # Try to map if it's a number or index
                                if correct_answer.isdigit():
                                    idx = int(correct_answer) - 1
                                    if 0 <= idx < 4:
                                        correct_answer = ["A", "B", "C", "D"][idx]
                                    else:
                                        print(f"Warning: Invalid correct_answer index {correct_answer}. Skipping question.")
                                        continue
                                else:
                                    print(f"Warning: Invalid correct_answer '{correct_answer}'. Skipping question.")
                                    continue
                            
                            # Determine health impact based on difficulty
                            health_impact = HEALTH_IMPACTS[difficulty]["correct"]
                            
                            questions.append({
                                "question": q["question"],
                                "difficulty": difficulty,
                                "options": options,
                                "correct_answer": correct_answer,
                                "health_impact": health_impact
                            })
                
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON response: {e}")
                    print(f"Response was: {response_text}")
                    # Fallback: create a simple question
                    questions.append(create_fallback_question(difficulty, truncated_text))
        
        # If no questions were generated, create fallback questions
        if not questions:
            questions = create_fallback_questions(truncated_text, num_easy, num_medium, num_hard)
        
        return questions
    
    except Exception as e:
        print(f"Error generating questions: {e}")
        # Return fallback questions if Snowflake fails
        return create_fallback_questions(pdf_text, num_easy, num_medium, num_hard)
    
    finally:
        cursor.close()

def create_fallback_question(difficulty: str, text: str) -> Dict:
    """Create a simple fallback question if LLM generation fails"""
    health_impact = HEALTH_IMPACTS[difficulty]["correct"]
    
    # Extract first sentence as question material
    sentences = text.split('.')[:3]
    topic = sentences[0][:50] if sentences else "the content"
    
    return {
        "question": f"Based on {topic}, what is the main topic discussed?",
        "difficulty": difficulty,
        "options": [
            "The main topic is clearly explained",
            "Multiple topics are discussed",
            "The topic requires further research",
            "The topic is not specified"
        ],
        "correct_answer": "A",
        "health_impact": health_impact
    }

def create_fallback_questions(text: str, num_easy: int, num_medium: int, num_hard: int) -> List[Dict]:
    """Create fallback questions if LLM generation completely fails"""
    questions = []
    
    for difficulty, count in [("easy", num_easy), ("medium", num_medium), ("hard", num_hard)]:
        for i in range(count):
            questions.append(create_fallback_question(difficulty, text))
    
    return questions

