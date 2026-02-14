# Quick Start Guide

## 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## 2. Configure Snowflake

Create a `.env` file in the `backend` directory:

```env
SNOWFLAKE_ACCOUNT=your_account_identifier
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=STUDY_BUDDY
SNOWFLAKE_SCHEMA=PUBLIC
```

## 3. Start the Server

```bash
python main.py
```

Or with auto-reload:
```bash
uvicorn main:app --reload --port 8000
```

## 4. Test the API

### Upload and Generate Questions (Combined Endpoint)

```bash
curl -X POST "http://localhost:8000/upload-and-generate?num_easy=2&num_medium=2&num_hard=1" \
  -F "file=@your_lecture_slides.pdf"
```

### Or use separate endpoints:

1. Upload PDF:
```bash
curl -X POST "http://localhost:8000/upload-pdf" \
  -F "file=@your_lecture_slides.pdf"
```

2. Generate Questions:
```bash
curl -X POST "http://localhost:8000/generate-questions" \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_text": "Your extracted text here...",
    "num_easy": 3,
    "num_medium": 3,
    "num_hard": 2
  }'
```

## 5. Frontend Integration

The API is configured with CORS to work with your React frontend. Make requests to:
- `http://localhost:8000/upload-and-generate` for the combined endpoint
- `http://localhost:8000/health-impacts` to get health impact values

## Health Impact System

- **Easy questions**: +5 health (correct), -2 health (wrong)
- **Medium questions**: +10 health (correct), -5 health (wrong)
- **Hard questions**: +20 health (correct), -10 health (wrong)

These values are returned in each question's `health_impact` field.

