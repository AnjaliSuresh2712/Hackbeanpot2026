# StudiGotchi (Study Buddy)

A study app that turns your PDFs (lecture slides, notes) into quiz questions. Upload a file, answer multiple-choice questions, and keep your tamagotchi-style pet healthy by getting answers right.

**Stack:** React (Vite) + FastAPI + Snowflake Cortex (LLM for question generation)

---

## How to get the game started

You need to run both the **frontend** and the **backend**. The frontend talks to the backend at `http://localhost:8000`.

### Prerequisites

- **Node.js** (v18 or newer) and **npm**
- **Python** (3.10 or newer) and **pip**
- A **Snowflake** account (free trial works) for AI-generated questions — see [Backend: Snowflake](#backend-snowflake) below

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd Hackbeanpot2026
```

### 2. Backend (API + question generation)

```bash
cd backend
```

Create a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

**Configure Snowflake** (required for the game to generate questions):

1. Copy the example env file and edit it with your values:
   ```bash
   cp .env.example .env
   ```
2. Open `backend/.env` and set:
   - `SNOWFLAKE_ACCOUNT` — your account identifier (e.g. `xy12345.us-east-1` from the Snowflake URL after login)
   - `SNOWFLAKE_USER` — your Snowflake username
   - `SNOWFLAKE_PASSWORD` — your Snowflake password
   - `SNOWFLAKE_WAREHOUSE` — e.g. `COMPUTE_WH` (create one in Snowflake if needed)
   - `SNOWFLAKE_DATABASE` — e.g. `STUDY_BUDDY` (create with `CREATE DATABASE STUDY_BUDDY;` in a Snowflake worksheet)
   - `SNOWFLAKE_SCHEMA` — e.g. `PUBLIC`

For detailed Snowflake setup (warehouse, database, Cortex permissions), see **[backend/SNOWFLAKE_SETUP.md](backend/SNOWFLAKE_SETUP.md)**.

Start the backend:

```bash
# From the backend directory, with venv activated
uvicorn main:app --reload --port 8000
```

Or: `python -m uvicorn main:app --reload --port 8000`

Leave this terminal running. The API will be at **http://localhost:8000**.

### 3. Frontend (React app)

Open a **new terminal** and run:

```bash
cd Hackbeanpot2026   # repo root
npm install
npm run dev
```

Vite will start the app (usually at **http://localhost:5173**). Open that URL in your browser.

### 4. Play

1. On the home screen, click **Feed!** and choose a **PDF** (lecture slides or notes with plenty of text).
2. Wait for the app to process the file and generate questions (via Snowflake Cortex).
3. Answer the multiple-choice questions. Your pet’s health goes up when you’re correct and down when you’re wrong.
4. Use **Go back** to upload a different PDF, or finish the set and choose **Continue** to play the same set again.

---

## Troubleshooting

- **503 when uploading** — Snowflake is not configured or the connection failed. Check `backend/.env` and that your Snowflake account identifier includes the region (e.g. `xy12345.us-east-1`). See [backend/SNOWFLAKE_SETUP.md](backend/SNOWFLAKE_SETUP.md).
- **400 “not enough extractable text”** — The PDF has too little text (e.g. image-only or very short). Use a document with more text (lecture notes, article).
- **Frontend can’t reach backend** — Ensure the backend is running on port 8000 and the frontend is calling `http://localhost:8000` (see `src/components/UploadBox.jsx` if you need to change the API URL).

---

## Project structure

- `src/` — React frontend (Vite)
- `backend/` — FastAPI server, PDF extraction, Snowflake Cortex question generation
- `backend/SNOWFLAKE_SETUP.md` — Step-by-step Snowflake setup
- `backend/QUICKSTART.md` — Backend-only quick reference
