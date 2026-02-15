from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv

from pdf_processor import extract_text_from_pdf
from question_generator import generate_questions

load_dotenv()

SNOWFLAKE_REQUIRED_MSG = (
    "Snowflake is not configured. Set SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, and SNOWFLAKE_PASSWORD in backend/.env to generate questions."
)


def get_snowflake_conn():
    """Create Snowflake connection from env. Returns None if not configured."""
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    user = os.getenv("SNOWFLAKE_USER")
    password = os.getenv("SNOWFLAKE_PASSWORD")
    if not all([account, user, password]):
        return None
    try:
        import snowflake.connector
        return snowflake.connector.connect(
            account=account,
            user=user,
            password=password,
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
            database=os.getenv("SNOWFLAKE_DATABASE", "STUDY_BUDDY"),
            schema=os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
        )
    except Exception as e:
        print(f"Snowflake connection failed: {e}")
        return None


app = FastAPI(title="Study Buddy API", version="1.0.0")

# CORS middleware to allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Question models (health_impact as object for frontend; correctIndex for QuizCard)
class Question(BaseModel):
    question: str
    difficulty: str  # "easy", "medium", "hard"
    options: List[str]
    correct_answer: str  # "A", "B", "C", or "D"
    correctIndex: Optional[int] = None  # 0-based index for frontend
    health_impact: Optional[Dict[str, int]] = None  # {"correct": n, "wrong": n}

    class Config:
        extra = "allow"  # allow correctIndex, health_impact from generator

class GenerateQuestionsRequest(BaseModel):
    pdf_text: str
    num_easy: int = 3
    num_medium: int = 3
    num_hard: int = 2

class QuestionResponse(BaseModel):
    questions: List[Question]
    total_questions: int

class HealthImpact(BaseModel):
    difficulty: str
    correct_answer_healing: int
    wrong_answer_damage: int

# Health impact configuration based on difficulty
HEALTH_IMPACTS = {
    "easy": {"correct": 5, "wrong": -2},
    "medium": {"correct": 10, "wrong": -5},
    "hard": {"correct": 20, "wrong": -10}
}

@app.get("/")
async def root():
    return {"message": "Study Buddy API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file and extract text from it.
    Returns the extracted text for question generation.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        # Save uploaded file temporarily
        contents = await file.read()
        temp_path = f"temp_{file.filename}"
        
        with open(temp_path, "wb") as f:
            f.write(contents)
        
        # Extract text from PDF
        text = extract_text_from_pdf(temp_path)
        
        # Clean up temp file
        os.remove(temp_path)
        
        if not text or len(text.strip()) < 100:
            raise HTTPException(
                status_code=400, 
                detail="PDF appears to be empty or could not extract sufficient text"
            )
        
        return {
            "filename": file.filename,
            "text_length": len(text),
            "text_preview": text[:500] + "..." if len(text) > 500 else text
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.post("/generate-questions")
async def generate_questions_endpoint(body: GenerateQuestionsRequest):
    """
    Generate questions from PDF text using Snowflake Cortex (real LLM).
    Requires Snowflake to be configured in .env.
    """
    pdf_text = (body.pdf_text or "").strip()
    if len(pdf_text) < 100:
        raise HTTPException(status_code=400, detail="PDF text is too short or empty")

    conn = get_snowflake_conn()
    if not conn:
        raise HTTPException(status_code=503, detail=SNOWFLAKE_REQUIRED_MSG)
    try:
        try:
            questions = generate_questions(
                pdf_text=pdf_text,
                num_easy=body.num_easy,
                num_medium=body.num_medium,
                num_hard=body.num_hard,
                snowflake_conn=conn,
            )
        finally:
            try:
                conn.close()
            except Exception:
                pass
        return QuestionResponse(questions=questions, total_questions=len(questions))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")

@app.post("/upload-and-generate")
async def upload_and_generate(
    file: UploadFile = File(...),
    num_easy: int = 3,
    num_medium: int = 3,
    num_hard: int = 2
):
    """
    Combined endpoint: Upload PDF, extract text, and generate questions in one call.
    Uses Snowflake Cortex for real questions; requires Snowflake to be configured.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    try:
        contents = await file.read()
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(contents)
        text = extract_text_from_pdf(temp_path)
        os.remove(temp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading PDF: {str(e)}")

    if not text or len(text.strip()) < 100:
        raise HTTPException(
            status_code=400,
            detail="PDF appears to be empty or could not extract sufficient text",
        )

    conn = get_snowflake_conn()
    if not conn:
        raise HTTPException(status_code=503, detail=SNOWFLAKE_REQUIRED_MSG)
    try:
        try:
            questions = generate_questions(
                pdf_text=text,
                num_easy=num_easy,
                num_medium=num_medium,
                num_hard=num_hard,
                snowflake_conn=conn,
            )
        finally:
            try:
                conn.close()
            except Exception:
                pass
        return QuestionResponse(questions=questions, total_questions=len(questions))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/health-impacts")
async def get_health_impacts():
    """Get the health impact configuration for each difficulty level"""
    return {
        "easy": HEALTH_IMPACTS["easy"],
        "medium": HEALTH_IMPACTS["medium"],
        "hard": HEALTH_IMPACTS["hard"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

