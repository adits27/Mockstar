# MockStar Speech Processing Backend — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the FastAPI speech processing backend for MockStar — transcribing interview audio with OpenAI Whisper, accumulating speech metrics via background tasks, and generating inclusive, profile-aware feedback with Gemini 2.0 Flash at session end.

**Architecture:** Each user turn POSTs an audio file; Whisper transcription is awaited (needed immediately for LLM question generation) and the transcript is returned right away. Speech analytics (filler words, pauses, WPM) run as a FastAPI BackgroundTask. At session end, all accumulated turn data is sent to Gemini 2.0 Flash, which generates a feedback report that is then persisted to Cloud SQL along with all transcripts. WPM is stored but excluded from the LLM feedback payload to avoid penalizing communication style differences. A user-reported profile (challenges, experience, goals) is injected into the feedback prompt as a bias-mitigation layer.

**Tech Stack:** FastAPI, OpenAI Whisper API (`openai` SDK), Gemini 2.0 Flash (`google-generativeai`), SQLAlchemy (asyncio), asyncpg, Alembic, Cloud SQL (PostgreSQL) in production / SQLite (aiosqlite) in tests, pytest, pytest-asyncio, httpx

---

## File Map

```
mockstar/
├── app/
│   ├── __init__.py
│   ├── main.py                        # FastAPI app + router registration
│   ├── config.py                      # Pydantic settings (env vars)
│   ├── database.py                    # Async SQLAlchemy engine + session factory
│   ├── models/
│   │   ├── __init__.py
│   │   └── db.py                      # ORM models: DBSession, DBTurn, DBFeedback
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── schemas.py                 # Pydantic request/response models
│   ├── store/
│   │   ├── __init__.py
│   │   └── session_store.py           # In-memory session store (module-level dict)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── analytics.py               # Filler detection, pause counting, WPM
│   │   ├── whisper.py                 # OpenAI Whisper API call
│   │   ├── feedback.py                # Gemini 2.0 Flash feedback generation
│   │   └── persistence.py             # Write completed session to Cloud SQL
│   └── routers/
│       ├── __init__.py
│       ├── sessions.py                # POST /sessions, GET /sessions, GET /sessions/{id}
│       └── turns.py                   # POST /sessions/{id}/turns, POST /sessions/{id}/end
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Shared fixtures: test client, DB override, mocks
│   ├── test_session_store.py
│   ├── test_analytics.py
│   ├── test_whisper.py
│   ├── test_feedback.py
│   ├── test_persistence.py
│   ├── test_sessions_router.py
│   └── test_turns_router.py
├── alembic/
│   ├── env.py
│   └── versions/
├── alembic.ini
├── requirements.txt
├── pytest.ini
└── .env.example
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `pytest.ini`
- Create: `.env.example`
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `app/main.py`

- [ ] **Step 1: Create `requirements.txt`**

```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
openai>=1.30.0
google-generativeai>=0.7.0
sqlalchemy[asyncio]>=2.0.30
asyncpg>=0.29.0
aiosqlite>=0.20.0
alembic>=1.13.0
pydantic>=2.7.0
pydantic-settings>=2.3.0
python-multipart>=0.0.9
pytest>=8.2.0
pytest-asyncio>=0.23.0
httpx>=0.27.0
pytest-mock>=3.14.0
```

- [ ] **Step 2: Create `pytest.ini`**

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

- [ ] **Step 3: Create `.env.example`**

```
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/mockstar
```

- [ ] **Step 4: Create `app/config.py`**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    google_api_key: str
    database_url: str

    class Config:
        env_file = ".env"


settings = Settings()
```

- [ ] **Step 5: Create `app/main.py`**

```python
from fastapi import FastAPI

app = FastAPI(title="MockStar Speech API")
```

- [ ] **Step 6: Create empty `__init__.py` files**

```bash
touch app/__init__.py app/models/__init__.py app/schemas/__init__.py \
      app/store/__init__.py app/services/__init__.py app/routers/__init__.py \
      tests/__init__.py
```

- [ ] **Step 7: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: all packages install without errors.

- [ ] **Step 8: Verify server starts**

```bash
uvicorn app.main:app --reload
```

Expected: `Application startup complete.` Visit `http://localhost:8000/docs` — empty Swagger UI loads.

- [ ] **Step 9: Commit**

```bash
git add requirements.txt pytest.ini .env.example app/
git commit -m "feat: scaffold FastAPI project with config and dependencies"
```

---

## Task 2: Database Models

**Files:**
- Create: `app/database.py`
- Create: `app/models/db.py`

- [ ] **Step 1: Create `app/database.py`**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with async_session_factory() as session:
        yield session
```

- [ ] **Step 2: Create `app/models/db.py`**

```python
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class DBSession(Base):
    __tablename__ = "sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False)
    job_role = Column(String)
    interview_type = Column(String)
    user_profile = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class DBTurn(Base):
    __tablename__ = "turns"

    turn_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.session_id"), nullable=False)
    turn_index = Column(Integer, nullable=False)
    question_text = Column(Text)
    transcript = Column(Text)
    filler_count = Column(Integer)
    filler_words = Column(JSONB)
    pause_count = Column(Integer)
    wpm = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class DBFeedback(Base):
    __tablename__ = "feedback"

    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("sessions.session_id"), nullable=False, unique=True
    )
    report = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 3: Commit**

```bash
git add app/database.py app/models/
git commit -m "feat: add SQLAlchemy async engine and ORM models"
```

---

## Task 3: Alembic Setup + First Migration

**Files:**
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/versions/<hash>_initial_schema.py` (auto-generated)

- [ ] **Step 1: Initialise Alembic**

```bash
alembic init alembic
```

Expected: `alembic/` directory and `alembic.ini` created.

- [ ] **Step 2: Replace `alembic/env.py` with async-compatible version**

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.models.db import Base
from app.config import settings

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 3: Generate migration (requires DATABASE_URL to be set)**

```bash
alembic revision --autogenerate -m "initial schema"
```

Expected: a new file in `alembic/versions/` with `sessions`, `turns`, and `feedback` table definitions.

- [ ] **Step 4: Apply migration**

```bash
alembic upgrade head
```

Expected: `Running upgrade  -> <hash>, initial schema`

- [ ] **Step 5: Commit**

```bash
git add alembic/ alembic.ini
git commit -m "feat: add Alembic migrations for sessions, turns, feedback tables"
```

---

## Task 4: Pydantic Schemas

**Files:**
- Create: `app/schemas/schemas.py`
- Create: `tests/test_schemas.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_schemas.py
import uuid
from app.schemas.schemas import (
    CreateSessionRequest,
    CreateSessionResponse,
    TurnResponse,
    SessionSummary,
    SessionDetail,
    FeedbackResponse,
)


def test_create_session_request_requires_user_id():
    req = CreateSessionRequest(
        user_id="user-1",
        job_role="Software Engineer",
        interview_type="technical",
        user_profile={"communication_challenges": ["stammer"], "experience_level": "junior"},
    )
    assert req.user_id == "user-1"
    assert req.user_profile["experience_level"] == "junior"


def test_turn_response_has_transcript():
    resp = TurnResponse(turn_id=str(uuid.uuid4()), transcript="I worked at Google.")
    assert resp.transcript == "I worked at Google."
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_schemas.py -v
```

Expected: `ImportError` — `schemas` module does not exist yet.

- [ ] **Step 3: Create `app/schemas/schemas.py`**

```python
from __future__ import annotations

from typing import Any
from pydantic import BaseModel


class UserProfile(BaseModel):
    communication_challenges: list[str] = []
    experience_level: str = "not specified"
    goals: str = "general improvement"


class CreateSessionRequest(BaseModel):
    user_id: str
    job_role: str = "not specified"
    interview_type: str = "general"
    user_profile: UserProfile | dict[str, Any] = {}


class CreateSessionResponse(BaseModel):
    session_id: str


class TurnResponse(BaseModel):
    turn_id: str
    transcript: str


class TurnSummary(BaseModel):
    turn_index: int
    question_text: str
    transcript: str
    filler_words: dict[str, int]
    pause_count: int
    wpm: float | None


class SessionSummary(BaseModel):
    session_id: str
    job_role: str
    interview_type: str
    created_at: str
    completed_at: str | None


class SessionDetail(BaseModel):
    session_id: str
    job_role: str
    interview_type: str
    user_profile: dict[str, Any]
    turns: list[TurnSummary]
    feedback: str | None


class FeedbackResponse(BaseModel):
    feedback: str
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_schemas.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add app/schemas/ tests/test_schemas.py
git commit -m "feat: add Pydantic request/response schemas"
```

---

## Task 5: In-Memory Session Store

**Files:**
- Create: `app/store/session_store.py`
- Create: `tests/test_session_store.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_session_store.py
import pytest
from app.store import session_store


@pytest.fixture(autouse=True)
def clear_store():
    session_store.clear()
    yield
    session_store.clear()


def test_create_and_get_session():
    session_store.create("sess-1", user_profile={"experience_level": "junior"}, metadata={"job_role": "SWE"})
    session = session_store.get("sess-1")
    assert session is not None
    assert session["metadata"]["job_role"] == "SWE"
    assert session["turns"] == []


def test_get_nonexistent_session_returns_none():
    assert session_store.get("missing") is None


def test_add_turn_appends_to_session():
    session_store.create("sess-2", user_profile={}, metadata={})
    session_store.add_turn("sess-2", {"turn_index": 0, "transcript": "Hello world", "filler_words": {}, "pause_count": 0, "wpm": 120.0})
    session = session_store.get("sess-2")
    assert len(session["turns"]) == 1
    assert session["turns"][0]["transcript"] == "Hello world"


def test_update_turn_metrics():
    session_store.create("sess-3", user_profile={}, metadata={})
    session_store.add_turn("sess-3", {"turn_index": 0, "transcript": "Um hello", "filler_words": {}, "pause_count": 0, "wpm": None})
    session_store.update_turn_metrics("sess-3", turn_index=0, filler_words={"um": 1}, pause_count=0, wpm=95.0)
    turn = session_store.get("sess-3")["turns"][0]
    assert turn["filler_words"] == {"um": 1}
    assert turn["wpm"] == 95.0


def test_delete_session():
    session_store.create("sess-4", user_profile={}, metadata={})
    session_store.delete("sess-4")
    assert session_store.get("sess-4") is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_session_store.py -v
```

Expected: `ImportError` or `AttributeError`.

- [ ] **Step 3: Create `app/store/session_store.py`**

```python
from typing import Any

_store: dict[str, dict] = {}


def clear() -> None:
    _store.clear()


def create(session_id: str, user_profile: dict, metadata: dict) -> None:
    _store[session_id] = {"user_profile": user_profile, "metadata": metadata, "turns": []}


def get(session_id: str) -> dict | None:
    return _store.get(session_id)


def add_turn(session_id: str, turn: dict[str, Any]) -> None:
    _store[session_id]["turns"].append(turn)


def update_turn_metrics(
    session_id: str,
    turn_index: int,
    filler_words: dict[str, int],
    pause_count: int,
    wpm: float,
) -> None:
    for turn in _store[session_id]["turns"]:
        if turn["turn_index"] == turn_index:
            turn["filler_words"] = filler_words
            turn["pause_count"] = pause_count
            turn["wpm"] = wpm
            return


def delete(session_id: str) -> None:
    _store.pop(session_id, None)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_session_store.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add app/store/ tests/test_session_store.py
git commit -m "feat: add in-memory session store with CRUD operations"
```

---

## Task 6: Speech Analytics Service

**Files:**
- Create: `app/services/analytics.py`
- Create: `tests/test_analytics.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_analytics.py
from app.services.analytics import detect_fillers, detect_pauses, calculate_wpm


def test_detect_fillers_counts_single_word_fillers():
    transcript = "I um worked at like Google and um left"
    result = detect_fillers(transcript)
    assert result["um"] == 2
    assert result["like"] == 1


def test_detect_fillers_counts_phrase_fillers():
    transcript = "It was you know kind of a big deal"
    result = detect_fillers(transcript)
    assert result["you know"] == 1
    assert result["kind of"] == 1


def test_detect_fillers_returns_empty_for_clean_speech():
    transcript = "My experience includes three years of backend development."
    result = detect_fillers(transcript)
    assert result == {}


def test_detect_fillers_is_case_insensitive():
    transcript = "Um that was Like a big deal"
    result = detect_fillers(transcript)
    assert result["um"] == 1
    assert result["like"] == 1


def test_detect_pauses_counts_gaps_above_threshold():
    words = [
        {"word": "hello", "start": 0.0, "end": 0.4},
        {"word": "world", "start": 2.0, "end": 2.4},   # 1.6s gap → pause
        {"word": "bye", "start": 2.5, "end": 2.8},     # 0.1s gap → no pause
    ]
    assert detect_pauses(words, threshold=1.5) == 1


def test_detect_pauses_returns_zero_for_fluent_speech():
    words = [
        {"word": "I", "start": 0.0, "end": 0.1},
        {"word": "speak", "start": 0.15, "end": 0.5},
        {"word": "fast", "start": 0.55, "end": 0.9},
    ]
    assert detect_pauses(words) == 0


def test_detect_pauses_returns_zero_for_empty_words():
    assert detect_pauses([]) == 0


def test_calculate_wpm_basic():
    assert calculate_wpm(word_count=150, duration_seconds=60.0) == 150.0


def test_calculate_wpm_rounds_to_one_decimal():
    assert calculate_wpm(word_count=100, duration_seconds=45.0) == 133.3


def test_calculate_wpm_returns_zero_for_zero_duration():
    assert calculate_wpm(word_count=10, duration_seconds=0.0) == 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_analytics.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Create `app/services/analytics.py`**

```python
import re

FILLER_PATTERNS: list[tuple[str, str]] = [
    ("you know", r"\byou know\b"),
    ("kind of", r"\bkind of\b"),
    ("sort of", r"\bsort of\b"),
    ("um", r"\bum\b"),
    ("uh", r"\buh\b"),
    ("like", r"\blike\b"),
    ("so", r"\bso\b"),
    ("basically", r"\bbasically\b"),
    ("literally", r"\bliterally\b"),
    ("actually", r"\bactually\b"),
    ("right", r"\bright\b"),
]


def detect_fillers(transcript: str) -> dict[str, int]:
    text = transcript.lower()
    counts: dict[str, int] = {}
    for label, pattern in FILLER_PATTERNS:
        matches = len(re.findall(pattern, text))
        if matches:
            counts[label] = matches
    return counts


def detect_pauses(words: list[dict], threshold: float = 1.5) -> int:
    if len(words) < 2:
        return 0
    return sum(
        1
        for i in range(1, len(words))
        if words[i]["start"] - words[i - 1]["end"] > threshold
    )


def calculate_wpm(word_count: int, duration_seconds: float) -> float:
    if duration_seconds == 0:
        return 0.0
    return round(word_count / duration_seconds * 60, 1)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_analytics.py -v
```

Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add app/services/analytics.py tests/test_analytics.py
git commit -m "feat: add speech analytics service (filler detection, pauses, WPM)"
```

---

## Task 7: Whisper Transcription Service

**Files:**
- Create: `app/services/whisper.py`
- Create: `tests/test_whisper.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_whisper.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.whisper import transcribe


@pytest.fixture
def mock_whisper_response():
    word1 = MagicMock()
    word1.word = "hello"
    word1.start = 0.0
    word1.end = 0.4

    word2 = MagicMock()
    word2.word = "world"
    word2.start = 0.5
    word2.end = 0.9

    response = MagicMock()
    response.text = "hello world"
    response.words = [word1, word2]
    response.duration = 1.0
    return response


async def test_transcribe_returns_transcript_and_words(mock_whisper_response):
    mock_file = MagicMock()
    mock_file.filename = "audio.webm"
    mock_file.content_type = "audio/webm"
    mock_file.read = AsyncMock(return_value=b"fake-audio-bytes")

    with patch("app.services.whisper.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.audio.transcriptions.create = AsyncMock(return_value=mock_whisper_response)

        result = await transcribe(mock_file)

    assert result["text"] == "hello world"
    assert result["duration"] == 1.0
    assert result["words"] == [
        {"word": "hello", "start": 0.0, "end": 0.4},
        {"word": "world", "start": 0.5, "end": 0.9},
    ]


async def test_transcribe_calls_whisper_with_verbose_json(mock_whisper_response):
    mock_file = MagicMock()
    mock_file.filename = "audio.webm"
    mock_file.content_type = "audio/webm"
    mock_file.read = AsyncMock(return_value=b"bytes")

    with patch("app.services.whisper.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        create_mock = AsyncMock(return_value=mock_whisper_response)
        instance.audio.transcriptions.create = create_mock

        await transcribe(mock_file)

        call_kwargs = create_mock.call_args.kwargs
        assert call_kwargs["model"] == "whisper-1"
        assert call_kwargs["response_format"] == "verbose_json"
        assert "word" in call_kwargs["timestamp_granularities"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_whisper.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Create `app/services/whisper.py`**

```python
from openai import AsyncOpenAI
from fastapi import UploadFile

from app.config import settings


async def transcribe(audio_file: UploadFile) -> dict:
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    audio_bytes = await audio_file.read()

    response = await client.audio.transcriptions.create(
        model="whisper-1",
        file=(audio_file.filename, audio_bytes, audio_file.content_type),
        response_format="verbose_json",
        timestamp_granularities=["word"],
    )

    return {
        "text": response.text,
        "words": [{"word": w.word, "start": w.start, "end": w.end} for w in response.words],
        "duration": response.duration,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_whisper.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add app/services/whisper.py tests/test_whisper.py
git commit -m "feat: add Whisper transcription service with word-level timestamps"
```

---

## Task 8: Gemini Feedback Service

**Files:**
- Create: `app/services/feedback.py`
- Create: `tests/test_feedback.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_feedback.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.feedback import build_feedback_prompt, generate_feedback


def test_build_feedback_prompt_includes_user_profile():
    session_data = {
        "user_profile": {
            "communication_challenges": ["stammer"],
            "experience_level": "junior",
            "goals": "land first SWE job",
        },
        "metadata": {"job_role": "Software Engineer", "interview_type": "technical"},
        "turns": [
            {
                "turn_index": 0,
                "question_text": "Tell me about yourself.",
                "transcript": "Um I worked at Google.",
                "filler_words": {"um": 1},
                "pause_count": 2,
            }
        ],
    }
    prompt = build_feedback_prompt(session_data)
    assert "stammer" in prompt
    assert "junior" in prompt
    assert "Software Engineer" in prompt
    assert "Tell me about yourself" in prompt
    assert "Um I worked at Google" in prompt
    assert "um" in prompt


def test_build_feedback_prompt_excludes_wpm():
    session_data = {
        "user_profile": {"communication_challenges": [], "experience_level": "senior", "goals": ""},
        "metadata": {"job_role": "PM", "interview_type": "behavioral"},
        "turns": [
            {
                "turn_index": 0,
                "question_text": "Describe a challenge.",
                "transcript": "I led a team.",
                "filler_words": {},
                "pause_count": 0,
                "wpm": 145.0,
            }
        ],
    }
    prompt = build_feedback_prompt(session_data)
    assert "145" not in prompt
    assert "wpm" not in prompt.lower()


async def test_generate_feedback_returns_model_text():
    session_data = {
        "user_profile": {"communication_challenges": [], "experience_level": "mid", "goals": ""},
        "metadata": {"job_role": "SWE", "interview_type": "technical"},
        "turns": [{"turn_index": 0, "question_text": "Q?", "transcript": "A.", "filler_words": {}, "pause_count": 0}],
    }

    mock_response = MagicMock()
    mock_response.text = "Great job on clarity."

    with patch("app.services.feedback.genai") as mock_genai:
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        result = await generate_feedback(session_data)

    assert result == "Great job on clarity."
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_feedback.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Create `app/services/feedback.py`**

```python
import google.generativeai as genai

from app.config import settings


def build_feedback_prompt(session_data: dict) -> str:
    profile = session_data["user_profile"]
    metadata = session_data["metadata"]
    turns = session_data["turns"]

    challenges = ", ".join(profile.get("communication_challenges", [])) or "none reported"
    experience = profile.get("experience_level", "not specified")
    goals = profile.get("goals", "general improvement")

    turns_text = "\n\n".join(
        f"Q{t['turn_index'] + 1}: {t['question_text']}\n"
        f"Answer: {t['transcript']}\n"
        f"Filler words: {t['filler_words'] or 'none detected'}\n"
        f"Significant pauses: {t['pause_count']}"
        for t in turns
    )

    return f"""You are an expert, inclusive interview coach.

User profile:
- Communication challenges: {challenges}
- Experience level: {experience}
- Goals: {goals}

Do not penalize the user for documented communication differences listed above.
Provide constructive, specific, and actionable feedback.

Interview context:
- Job role: {metadata.get("job_role", "not specified")}
- Interview type: {metadata.get("interview_type", "general")}

Interview turns:
{turns_text}

Generate a structured feedback report in markdown covering:
1. Content quality and relevance of answers
2. Communication clarity
3. Filler word patterns (frame constructively, not punitively)
4. Strengths observed
5. Specific areas for improvement with actionable suggestions
"""


async def generate_feedback(session_data: dict) -> str:
    genai.configure(api_key=settings.google_api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = build_feedback_prompt(session_data)
    response = await model.generate_content_async(prompt)
    return response.text
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_feedback.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add app/services/feedback.py tests/test_feedback.py
git commit -m "feat: add Gemini feedback service with inclusive prompt design"
```

---

## Task 9: Database Persistence Service

**Files:**
- Create: `app/services/persistence.py`
- Create: `tests/test_persistence.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_persistence.py
import pytest
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from app.models.db import Base, DBSession, DBTurn, DBFeedback
from app.services.persistence import persist_completed_session

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


async def test_persist_completed_session_writes_all_tables(db_session):
    session_id = str(uuid.uuid4())
    session_data = {
        "user_profile": {"communication_challenges": ["stammer"], "experience_level": "junior"},
        "metadata": {"user_id": "user-1", "job_role": "SWE", "interview_type": "technical"},
        "turns": [
            {
                "turn_index": 0,
                "question_text": "Tell me about yourself.",
                "transcript": "Um I worked at Google.",
                "filler_words": {"um": 1},
                "filler_count": 1,
                "pause_count": 2,
                "wpm": 130.0,
            }
        ],
    }
    feedback_text = "Great communication overall."

    await persist_completed_session(db_session, session_id, session_data, feedback_text)

    db_sess = await db_session.get(DBSession, uuid.UUID(session_id))
    assert db_sess is not None
    assert db_sess.job_role == "SWE"
    assert db_sess.completed_at is not None

    result = await db_session.execute(
        select(DBTurn).where(DBTurn.session_id == uuid.UUID(session_id))
    )
    turns = result.scalars().all()
    assert len(turns) == 1
    assert turns[0].transcript == "Um I worked at Google."
    assert turns[0].wpm == 130.0

    result = await db_session.execute(
        select(DBFeedback).where(DBFeedback.session_id == uuid.UUID(session_id))
    )
    feedback = result.scalar_one()
    assert feedback.report == "Great communication overall."
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_persistence.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Create `app/services/persistence.py`**

```python
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import DBSession, DBTurn, DBFeedback


async def persist_completed_session(
    db: AsyncSession,
    session_id: str,
    session_data: dict,
    feedback_text: str,
) -> None:
    metadata = session_data["metadata"]
    sid = uuid.UUID(session_id)

    db_session = DBSession(
        session_id=sid,
        user_id=metadata.get("user_id", ""),
        job_role=metadata.get("job_role"),
        interview_type=metadata.get("interview_type"),
        user_profile=session_data.get("user_profile", {}),
        completed_at=datetime.utcnow(),
    )
    db.add(db_session)

    for turn in session_data.get("turns", []):
        filler_words = turn.get("filler_words", {})
        db_turn = DBTurn(
            session_id=sid,
            turn_index=turn["turn_index"],
            question_text=turn.get("question_text"),
            transcript=turn.get("transcript"),
            filler_count=sum(filler_words.values()),
            filler_words=filler_words,
            pause_count=turn.get("pause_count"),
            wpm=turn.get("wpm"),
        )
        db.add(db_turn)

    db_feedback = DBFeedback(session_id=sid, report=feedback_text)
    db.add(db_feedback)

    await db.commit()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_persistence.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add app/services/persistence.py tests/test_persistence.py
git commit -m "feat: add DB persistence service for completed sessions"
```

---

## Task 10: Sessions Router

**Files:**
- Create: `app/routers/sessions.py`
- Create: `tests/conftest.py`
- Create: `tests/test_sessions_router.py`
- Modify: `app/main.py`

- [ ] **Step 1: Create `tests/conftest.py`**

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.store import session_store


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture(autouse=True)
def clear_store():
    session_store.clear()
    yield
    session_store.clear()
```

- [ ] **Step 2: Write failing tests**

```python
# tests/test_sessions_router.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select


async def test_create_session_returns_session_id(client):
    with patch("app.routers.sessions.get_db"):
        resp = await client.post("/sessions", json={
            "user_id": "user-1",
            "job_role": "Software Engineer",
            "interview_type": "technical",
            "user_profile": {"communication_challenges": [], "experience_level": "junior"},
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert len(data["session_id"]) == 36  # UUID format


async def test_create_session_stores_in_memory(client):
    from app.store import session_store
    with patch("app.routers.sessions.get_db"):
        resp = await client.post("/sessions", json={
            "user_id": "user-1",
            "job_role": "SWE",
            "interview_type": "behavioral",
            "user_profile": {},
        })
    session_id = resp.json()["session_id"]
    assert session_store.get(session_id) is not None


async def test_get_sessions_returns_list(client):
    from app.store import session_store
    import uuid

    mock_db_sessions = [
        MagicMock(
            session_id=uuid.uuid4(),
            job_role="SWE",
            interview_type="technical",
            created_at=MagicMock(__str__=lambda s: "2026-05-07T10:00:00"),
            completed_at=None,
        )
    ]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_db_sessions
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    async def override_db():
        yield mock_db

    from app.main import app
    from app.database import get_db
    app.dependency_overrides[get_db] = override_db

    resp = await client.get("/sessions?user_id=user-1")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    app.dependency_overrides.clear()
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/test_sessions_router.py -v
```

Expected: 404 or `ImportError`.

- [ ] **Step 4: Create `app/routers/sessions.py`**

```python
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db import DBSession
from app.schemas.schemas import CreateSessionRequest, CreateSessionResponse, SessionSummary
from app.store import session_store

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=CreateSessionResponse)
async def create_session(body: CreateSessionRequest, db: AsyncSession = Depends(get_db)):
    session_id = str(uuid.uuid4())
    profile = body.user_profile if isinstance(body.user_profile, dict) else body.user_profile.model_dump()
    session_store.create(
        session_id,
        user_profile=profile,
        metadata={
            "user_id": body.user_id,
            "job_role": body.job_role,
            "interview_type": body.interview_type,
        },
    )
    return CreateSessionResponse(session_id=session_id)


@router.get("", response_model=list[SessionSummary])
async def list_sessions(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DBSession).where(DBSession.user_id == user_id))
    rows = result.scalars().all()
    return [
        SessionSummary(
            session_id=str(row.session_id),
            job_role=row.job_role or "",
            interview_type=row.interview_type or "",
            created_at=str(row.created_at),
            completed_at=str(row.completed_at) if row.completed_at else None,
        )
        for row in rows
    ]


@router.get("/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    row = await db.get(DBSession, uuid.UUID(session_id))
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Session not found")

    from sqlalchemy import select as sa_select
    from app.models.db import DBTurn, DBFeedback

    turns_result = await db.execute(
        sa_select(DBTurn).where(DBTurn.session_id == uuid.UUID(session_id)).order_by(DBTurn.turn_index)
    )
    turns = turns_result.scalars().all()

    feedback_result = await db.execute(
        sa_select(DBFeedback).where(DBFeedback.session_id == uuid.UUID(session_id))
    )
    feedback = feedback_result.scalar_one_or_none()

    return {
        "session_id": session_id,
        "job_role": row.job_role,
        "interview_type": row.interview_type,
        "user_profile": row.user_profile or {},
        "turns": [
            {
                "turn_index": t.turn_index,
                "question_text": t.question_text,
                "transcript": t.transcript,
                "filler_words": t.filler_words or {},
                "pause_count": t.pause_count,
                "wpm": t.wpm,
            }
            for t in turns
        ],
        "feedback": feedback.report if feedback else None,
    }
```

- [ ] **Step 5: Register router in `app/main.py`**

```python
from fastapi import FastAPI
from app.routers import sessions

app = FastAPI(title="MockStar Speech API")
app.include_router(sessions.router)
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_sessions_router.py -v
```

Expected: 3 passed.

- [ ] **Step 7: Commit**

```bash
git add app/routers/sessions.py app/main.py tests/conftest.py tests/test_sessions_router.py
git commit -m "feat: add sessions router (create, list, get)"
```

---

## Task 11: Turns Router — POST /turns (Transcript Fast Path)

**Files:**
- Create: `app/routers/turns.py`
- Modify: `app/main.py`
- Create: `tests/test_turns_router.py` (POST /turns tests)

- [ ] **Step 1: Write failing tests**

```python
# tests/test_turns_router.py
import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from app.store import session_store


@pytest.fixture
def session_id():
    sid = str(uuid.uuid4())
    session_store.create(sid, user_profile={}, metadata={"job_role": "SWE", "interview_type": "technical"})
    return sid


async def test_post_turn_returns_transcript(client, session_id):
    mock_whisper = {"text": "I worked at Google.", "words": [], "duration": 3.0}

    with patch("app.routers.turns.transcribe", AsyncMock(return_value=mock_whisper)), \
         patch("app.routers.turns.BackgroundTasks.add_task"):
        resp = await client.post(
            f"/sessions/{session_id}/turns",
            data={"question_text": "Tell me about yourself.", "turn_index": "0"},
            files={"audio": ("audio.webm", b"fake-bytes", "audio/webm")},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["transcript"] == "I worked at Google."
    assert "turn_id" in data


async def test_post_turn_returns_404_for_unknown_session(client):
    with patch("app.routers.turns.transcribe", AsyncMock(return_value={"text": "x", "words": [], "duration": 1.0})):
        resp = await client.post(
            "/sessions/nonexistent-id/turns",
            data={"question_text": "Q?", "turn_index": "0"},
            files={"audio": ("audio.webm", b"bytes", "audio/webm")},
        )
    assert resp.status_code == 404


async def test_post_turn_stores_transcript_in_session_store(client, session_id):
    mock_whisper = {"text": "My background is in ML.", "words": [], "duration": 4.0}

    with patch("app.routers.turns.transcribe", AsyncMock(return_value=mock_whisper)):
        await client.post(
            f"/sessions/{session_id}/turns",
            data={"question_text": "Background?", "turn_index": "0"},
            files={"audio": ("audio.webm", b"bytes", "audio/webm")},
        )

    session = session_store.get(session_id)
    assert len(session["turns"]) == 1
    assert session["turns"][0]["transcript"] == "My background is in ML."
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_turns_router.py::test_post_turn_returns_transcript \
       tests/test_turns_router.py::test_post_turn_returns_404_for_unknown_session \
       tests/test_turns_router.py::test_post_turn_stores_transcript_in_session_store -v
```

Expected: 404 errors or `ImportError`.

- [ ] **Step 3: Create `app/routers/turns.py`**

```python
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.schemas import TurnResponse, FeedbackResponse
from app.services import analytics as analytics_svc
from app.services.whisper import transcribe
from app.store import session_store

router = APIRouter(prefix="/sessions", tags=["turns"])


def _run_analytics(session_id: str, turn_index: int, whisper_result: dict) -> None:
    words = whisper_result.get("words", [])
    duration = whisper_result.get("duration", 0)
    transcript = whisper_result.get("text", "")

    filler_words = analytics_svc.detect_fillers(transcript)
    pause_count = analytics_svc.detect_pauses(words)
    wpm = analytics_svc.calculate_wpm(len(words), duration)

    session_store.update_turn_metrics(session_id, turn_index, filler_words, pause_count, wpm)


@router.post("/{session_id}/turns", response_model=TurnResponse)
async def post_turn(
    session_id: str,
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    question_text: str = Form(...),
    turn_index: int = Form(...),
):
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    whisper_result = await transcribe(audio)
    transcript = whisper_result["text"]
    turn_id = str(uuid.uuid4())

    session_store.add_turn(session_id, {
        "turn_id": turn_id,
        "turn_index": turn_index,
        "question_text": question_text,
        "transcript": transcript,
        "filler_words": {},
        "pause_count": 0,
        "wpm": None,
    })

    background_tasks.add_task(_run_analytics, session_id, turn_index, whisper_result)

    return TurnResponse(turn_id=turn_id, transcript=transcript)
```

- [ ] **Step 4: Register turns router in `app/main.py`**

```python
from fastapi import FastAPI
from app.routers import sessions, turns

app = FastAPI(title="MockStar Speech API")
app.include_router(sessions.router)
app.include_router(turns.router)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_turns_router.py::test_post_turn_returns_transcript \
       tests/test_turns_router.py::test_post_turn_returns_404_for_unknown_session \
       tests/test_turns_router.py::test_post_turn_stores_transcript_in_session_store -v
```

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add app/routers/turns.py app/main.py tests/test_turns_router.py
git commit -m "feat: add POST /sessions/{id}/turns with async analytics background task"
```

---

## Task 12: End Interview Endpoint — POST /end

**Files:**
- Modify: `app/routers/turns.py`
- Modify: `tests/test_turns_router.py`

- [ ] **Step 1: Write failing tests (append to `tests/test_turns_router.py`)**

```python
async def test_post_end_returns_feedback(client, session_id):
    session_store.add_turn(session_id, {
        "turn_id": "t1",
        "turn_index": 0,
        "question_text": "Tell me about yourself.",
        "transcript": "I worked at Google for three years.",
        "filler_words": {"um": 1},
        "pause_count": 1,
        "wpm": 140.0,
    })

    mock_feedback = "Strong answers overall. Work on reducing filler words."

    with patch("app.routers.turns.generate_feedback", AsyncMock(return_value=mock_feedback)), \
         patch("app.routers.turns.persist_completed_session", AsyncMock()), \
         patch("app.routers.turns.get_db"):
        resp = await client.post(f"/sessions/{session_id}/end")

    assert resp.status_code == 200
    assert resp.json()["feedback"] == mock_feedback


async def test_post_end_returns_404_for_unknown_session(client):
    with patch("app.routers.turns.get_db"):
        resp = await client.post("/sessions/does-not-exist/end")
    assert resp.status_code == 404


async def test_post_end_clears_session_from_memory(client, session_id):
    session_store.add_turn(session_id, {
        "turn_id": "t1", "turn_index": 0, "question_text": "Q?",
        "transcript": "A.", "filler_words": {}, "pause_count": 0, "wpm": 100.0,
    })

    with patch("app.routers.turns.generate_feedback", AsyncMock(return_value="Feedback.")), \
         patch("app.routers.turns.persist_completed_session", AsyncMock()), \
         patch("app.routers.turns.get_db"):
        await client.post(f"/sessions/{session_id}/end")

    assert session_store.get(session_id) is None
```

- [ ] **Step 2: Run new tests to verify they fail**

```bash
pytest tests/test_turns_router.py::test_post_end_returns_feedback \
       tests/test_turns_router.py::test_post_end_returns_404_for_unknown_session \
       tests/test_turns_router.py::test_post_end_clears_session_from_memory -v
```

Expected: 404 or `AttributeError` — `/end` does not exist yet.

- [ ] **Step 3: Add `/end` endpoint to `app/routers/turns.py`**

Add the following import at the top of `app/routers/turns.py`:

```python
from app.services.feedback import generate_feedback
from app.services.persistence import persist_completed_session
```

Add the following endpoint after `post_turn`:

```python
@router.post("/{session_id}/end", response_model=FeedbackResponse)
async def end_interview(session_id: str, db: AsyncSession = Depends(get_db)):
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    feedback_text = await generate_feedback(session)
    await persist_completed_session(db, session_id, session, feedback_text)
    session_store.delete(session_id)

    return FeedbackResponse(feedback=feedback_text)
```

Also add the missing import at the top:

```python
from app.database import get_db
```

- [ ] **Step 4: Run all tests to verify everything passes**

```bash
pytest tests/ -v
```

Expected: all tests pass. Confirm counts match: test_schemas (2), test_session_store (5), test_analytics (9), test_whisper (2), test_feedback (3), test_persistence (1), test_sessions_router (3), test_turns_router (6) = **31 passed**.

- [ ] **Step 5: Commit**

```bash
git add app/routers/turns.py tests/test_turns_router.py
git commit -m "feat: add POST /sessions/{id}/end — generate feedback, persist, clear store"
```

---

## Self-Review

**Spec coverage:**
- ✅ Batch processing — all audio processed per-turn, not streamed
- ✅ Conversational session model — turns accumulate, feedback at end
- ✅ Whisper word-level timestamps — `timestamp_granularities=["word"]` in Task 7
- ✅ Background analytics — `BackgroundTasks.add_task(_run_analytics, ...)` in Task 11
- ✅ WPM stored, excluded from LLM — `calculate_wpm` stored in session store; not in `build_feedback_prompt`
- ✅ User profile in feedback prompt — injected in `build_feedback_prompt` (Task 8)
- ✅ GCP Cloud SQL persistence — `persist_completed_session` writes sessions/turns/feedback (Task 9)
- ✅ No audio persistence — audio discarded after `transcribe()` returns
- ✅ Gemini 2.0 Flash — `genai.GenerativeModel("gemini-2.0-flash")` in Task 8
- ✅ All five endpoints — POST /sessions, POST /turns, POST /end, GET /sessions, GET /sessions/{id}
- ✅ Error handling — 404 for missing session, 502 pattern documented in spec (Whisper/Gemini failures handled by FastAPI default 500; can be extended)

**No placeholders found.**

**Type consistency verified** — `session_store` functions use the same dict shape across Tasks 5, 11, 12. `whisper_result` keys (`text`, `words`, `duration`) are consistent between Task 7 (producer) and Task 11 (consumer).
