# MockStar

AI-powered interview preparation platform with multimodal feedback. MockStar simulates realistic interview conversations and provides personalized coaching based on speech analysis and non-verbal communication cues.

## Overview

MockStar conducts dynamic mock interviews using a conversational AI interviewer that follows up based on your responses. At the end of each session, you receive a structured feedback report covering content quality, communication patterns, and specific areas for improvement.

The platform is designed to be accessible and inclusive. Users can self-report communication differences (stammer, lisp, accent, etc.) so the feedback engine can contextualize its analysis rather than penalize natural variation in speech.

## Architecture

The system is composed of three independent modules:

- **Speech Processing** -- transcription via OpenAI Whisper, speech analytics (filler words, pauses, speaking rate), and feedback generation via Gemini 2.0 Flash
- **Computer Vision** -- face detection, head pose estimation, and gaze analysis via OpenCV and MediaPipe (in development)
- **Frontend** -- React web interface for video/audio capture, interview interaction, and feedback display (in development)

This repository contains the speech processing backend.

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| Speech-to-text | OpenAI Whisper API |
| Feedback generation | Gemini 2.0 Flash |
| Database | GCP Cloud SQL (PostgreSQL) |
| Migrations | Alembic |
| Testing | pytest, pytest-asyncio |

## Project Structure

```
app/
├── config.py              Environment-based configuration
├── main.py                FastAPI application entry point
├── database.py            Async SQLAlchemy engine and session factory
├── models/db.py           ORM models (sessions, turns, feedback)
├── schemas/schemas.py     Pydantic request and response models
├── store/session_store.py In-memory store for active interview sessions
├── services/
│   ├── analytics.py       Filler word detection, pause counting, WPM
│   ├── whisper.py         OpenAI Whisper transcription service
│   ├── feedback.py        Gemini feedback generation with inclusive prompting
│   └── persistence.py     Persists completed sessions to Cloud SQL
└── routers/
    ├── sessions.py        Session lifecycle endpoints
    └── turns.py           Turn submission and interview end endpoints

alembic/                   Database migrations
tests/                     Full test suite (32 tests)
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/sessions` | Create a new interview session |
| GET | `/sessions?user_id=` | List past sessions for a user |
| GET | `/sessions/{id}` | Get session detail with transcripts and feedback |
| POST | `/sessions/{id}/turns` | Submit a recorded answer, returns transcript |
| POST | `/sessions/{id}/end` | End the interview and generate feedback report |

### Turn Flow

Each `POST /turns` call accepts an audio file and returns a transcript immediately. Speech analytics (filler words, pauses, speaking rate) are computed in the background so they do not add latency to the conversation. At `POST /end`, all accumulated turn data is passed to Gemini 2.0 Flash to generate the feedback report, which is then persisted to Cloud SQL.

Speaking rate (WPM) is stored for reference but is intentionally excluded from the feedback prompt to avoid penalizing users based on pace.

## Setup

### Requirements

- Python 3.9+
- A GCP Cloud SQL (PostgreSQL) instance
- OpenAI API key
- Google AI API key

### Installation

```bash
pip install -r requirements.txt
```

### Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/mockstar
```

### Database Setup

```bash
alembic upgrade head
```

### Running the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive documentation is at `http://localhost:8000/docs`.

## Testing

```bash
pytest
```

All 32 tests run without a live database or API credentials. External services are mocked at the test boundary.

