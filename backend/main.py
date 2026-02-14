from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
import snowflake.connector
from pdf_processor import extract_text_from_pdf
from question_generator import generate_questions

load_dotenv()

app = FastAPI(title="Study Buddy API", version="1.0.0")

# CORS middleware to allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Snowflake connection configuration
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "STUDY_BUDDY")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")

# Question models
class Question(BaseModel):
    question: str
    difficulty: str  # "easy", "medium", "hard"
    options: List[str]
    correct_answer: str
    health_impact: int  # Positive for correct answer (healing), negative for wrong (damage)

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

def get_snowflake_connection():
    """Create and return a Snowflake connection"""
    if not all([SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD]):
        raise HTTPException(
            status_code=500, 
            detail="Snowflake credentials not configured. Please set SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, and SNOWFLAKE_PASSWORD in .env file"
        )
    
    try:
        conn = snowflake.connector.connect(
            user=SNOWFLAKE_USER,
            password=SNOWFLAKE_PASSWORD,
            account=SNOWFLAKE_ACCOUNT,
            warehouse=SNOWFLAKE_WAREHOUSE,
            database=SNOWFLAKE_DATABASE,
            schema=SNOWFLAKE_SCHEMA
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to Snowflake: {str(e)}")

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
async def generate_questions_endpoint(
    pdf_text: str,
    num_easy: int = 3,
    num_medium: int = 3,
    num_hard: int = 2
):
    """
    Generate questions from PDF text using Snowflake Cortex LLM.
    
    Args:
        pdf_text: The extracted text from the PDF
        num_easy: Number of easy questions to generate
        num_medium: Number of medium questions to generate
        num_hard: Number of hard questions to generate
    """
    if not pdf_text or len(pdf_text.strip()) < 100:
        raise HTTPException(status_code=400, detail="PDF text is too short or empty")
    
    try:
        # Generate questions using Snowflake Cortex
        questions = generate_questions(
            pdf_text=pdf_text,
            num_easy=num_easy,
            num_medium=num_medium,
            num_hard=num_hard,
            snowflake_conn=get_snowflake_connection()
        )
        
        return QuestionResponse(
            questions=questions,
            total_questions=len(questions)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating questions: {str(e)}"
        )

@app.post("/upload-and-generate")
async def upload_and_generate(
    file: UploadFile = File(...),
    num_easy: int = 3,
    num_medium: int = 3,
    num_hard: int = 2
):
    """
    Combined endpoint: Upload PDF, extract text, and generate questions in one call.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        # Save and extract text
        contents = await file.read()
        temp_path = f"temp_{file.filename}"
        
        with open(temp_path, "wb") as f:
            f.write(contents)
        
        text = extract_text_from_pdf(temp_path)
        os.remove(temp_path)
        
        if not text or len(text.strip()) < 100:
            raise HTTPException(
                status_code=400, 
                detail="PDF appears to be empty or could not extract sufficient text"
            )
        
        # Generate questions
        questions = generate_questions(
            pdf_text=text,
            num_easy=num_easy,
            num_medium=num_medium,
            num_hard=num_hard,
            snowflake_conn=get_snowflake_connection()
        )
        
        return QuestionResponse(
            questions=questions,
            total_questions=len(questions)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing request: {str(e)}"
        )

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

