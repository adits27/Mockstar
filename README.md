# MockStar

AI-powered interview preparation platform with multimodal feedback. MockStar simulates realistic interview conversations and provides personalised coaching based on speech analysis, computer vision, and your own resume.

## Overview

MockStar conducts dynamic mock interviews using a conversational AI interviewer that adapts follow-up questions based on your responses and resume. At the end of each session, you receive a structured feedback report covering content quality, communication patterns, and specific resume-grounded story suggestions.

The platform is designed to be accessible and inclusive. Users can self-report communication differences (stammer, lisp, accent, etc.) so the feedback engine contextualises its analysis rather than penalise natural variation in speech.

## Architecture

```
frontend/          Next.js 16 web app (Google auth, interview UI, feedback dashboard)
app/               FastAPI backend
alembic/           Database migrations
tests/             Backend test suite
```

**Backend services:**
- **Speech processing** — transcription via OpenAI Whisper, speech analytics (filler words, pauses, WPM)
- **Computer vision** — gaze tracking and confidence scoring via OpenCV (runs per-turn as a background task)
- **AI interviewer** — Gemini 2.5 Flash generates contextual follow-up questions tailored to role, JD, and resume
- **Feedback generation** — Gemini 2.5 Flash produces structured scores and resume-aware feedback

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, TypeScript, Tailwind CSS |
| Auth | Auth.js v5 (Google OAuth) |
| API | FastAPI |
| Speech-to-text | OpenAI Whisper API |
| AI (questions + feedback) | Gemini 2.5 Flash |
| Computer vision | OpenCV (Haar cascades) |
| Database | GCP Cloud SQL (PostgreSQL) |
| Migrations | Alembic |
| Testing | pytest, pytest-asyncio |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/sessions` | Create a new interview session |
| GET | `/sessions?user_id=` | List completed sessions for a user |
| GET | `/sessions/{id}` | Get session detail with transcripts and feedback |
| POST | `/sessions/{id}/turns` | Submit audio (+ optional video), returns transcript |
| POST | `/sessions/{id}/next-question` | Generate next interview question |
| POST | `/sessions/{id}/end` | End interview and generate feedback report |
| POST | `/users/{user_id}/resume` | Upload and parse a resume (PDF or DOCX) |
| GET | `/users/{user_id}/resume` | Fetch parsed resume text |
| POST | `/users/{user_id}/extract-text` | Extract text from a PDF/DOCX (used for JD upload) |

## Setup

### Requirements

- Python 3.9+
- Node.js 18+
- A PostgreSQL instance (GCP Cloud SQL or local via Docker)
- OpenAI API key
- Google AI API key
- Google OAuth credentials (for frontend auth)

### Backend

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/mockstar
```

Run migrations:
```bash
alembic upgrade head
```

Start the server:
```bash
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:
```
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
AUTH_SECRET=<run: npx auth secret>
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Start the dev server:
```bash
npm run dev
```

App available at `http://localhost:3000`.

### Google OAuth setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com) → APIs & Services → Credentials
2. Create an OAuth client ID (Web application)
3. Authorised JavaScript origins: `http://localhost:3000`
4. Authorised redirect URIs: `http://localhost:3000/api/auth/callback/google`
