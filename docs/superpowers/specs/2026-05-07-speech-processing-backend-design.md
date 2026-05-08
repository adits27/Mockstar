# MockStar — Speech Processing Backend Design

**Date:** 2026-05-07  
**Author:** Adithya Subramaniam  
**Scope:** Speech processing pipeline, session management, and feedback generation backend. Vision/multimodal module is out of scope for this spec.

---

## 1. Overview

MockStar's speech processing backend handles the full lifecycle of a mock interview session: receiving audio from the user's browser, transcribing it, accumulating speech analytics silently in the background, and generating a personalized, inclusive feedback report at the end. It is designed to keep the conversational interview flow fast while deferring analytics work so it never blocks the user from receiving the next question.

---

## 2. Core Design Principles

- **Transcript-first:** Whisper transcription is the only blocking operation per turn. Everything else is async.
- **Collect broadly, curate for feedback:** All metrics are stored, but only non-penalizing metrics are sent to the LLM for feedback generation (WPM excluded).
- **Inclusive by design:** User self-reported communication profile (stammer, lisp, ESL, etc.) is persisted with the session and injected into the LLM feedback prompt to prevent algorithmic bias.
- **No audio persistence:** Audio files are discarded immediately after transcription. Only transcripts and feedback are stored.

---

## 3. Tech Stack

| Component | Choice | Reason |
|---|---|---|
| Backend framework | FastAPI | Async-native, lightweight, strong background task support |
| Speech-to-text | OpenAI Whisper API | Managed, word-level timestamps via `verbose_json`, no GPU needed |
| LLM (questions + feedback) | Gemini 2.0 Flash | GCP-native, generous free tier, multimodal (ready for vision module) |
| Active session store | In-memory Python dict | Zero-latency, sufficient for short-lived interview sessions |
| Persistence | GCP Cloud SQL (PostgreSQL) | Managed, GCP-native, stores transcripts and feedback only |
| ORM | SQLAlchemy (async) | Standard, works cleanly with Cloud SQL |

---

## 4. System Architecture

```
Browser (React)
    │
    │  POST /sessions                    → create session
    │  POST /sessions/{id}/turns         → upload audio per turn, returns transcript
    │  POST /sessions/{id}/end           → end interview, returns feedback report
    │  GET  /sessions                    → list user's past sessions
    │  GET  /sessions/{id}              → get session detail (turns + feedback)
    ▼
FastAPI Backend
    │
    ├── Turn Handler  (POST /sessions/{id}/turns)
    │     ├── [await]      OpenAI Whisper API  →  transcript
    │     ├── [return]     transcript  →  caller (LLM generates next question)
    │     └── [background] Speech Analytics    →  metrics written to in-memory store
    │
    ├── In-Memory Session Store
    │     └── { session_id: { turns: [...], user_profile: {...}, metadata: {...} } }
    │
    ├── Feedback Handler  (POST /sessions/{id}/end)
    │     ├── flush pending background tasks
    │     ├── build LLM payload (transcripts + filler words + pauses + user profile)
    │     ├── [await] Gemini 2.0 Flash  →  feedback report
    │     └── [await] persist session + turns + feedback  →  Cloud SQL
    │
    └── GCP Cloud SQL (PostgreSQL)
          ├── sessions
          ├── turns
          └── feedback
```

**Key invariant:** The `POST /turns` endpoint returns as soon as Whisper responds. Speech analytics never add latency to the conversational flow.

---

## 5. API Endpoints

### `POST /sessions`
Create a new interview session.

**Request body:**
```json
{
  "user_id": "string",
  "job_role": "string",
  "interview_type": "string",
  "user_profile": {
    "communication_challenges": ["stammer", "ESL"],
    "experience_level": "junior",
    "goals": "string"
  }
}
```

**Response:**
```json
{ "session_id": "uuid" }
```

---

### `POST /sessions/{session_id}/turns`
Upload audio for a single user turn. Returns transcript immediately; analytics run in background.

**Request:** `multipart/form-data`
- `audio`: audio file (WebM/WAV from browser MediaRecorder)
- `question_text`: the question the AI asked this turn
- `turn_index`: integer ordering within the session

**Response (fast path — returned as soon as Whisper completes):**
```json
{
  "turn_id": "uuid",
  "transcript": "string"
}
```

**Background task (does not block response):**
- Extract filler words, pause count, WPM from Whisper word timestamps
- Write metrics to in-memory session store

---

### `POST /sessions/{session_id}/end`
End the interview. Flushes analytics, generates feedback, persists everything.

**Response:**
```json
{
  "feedback": "string (markdown report from Gemini)"
}
```

---

### `GET /sessions`
List all past sessions for a user.

**Query params:** `user_id`

**Response:** Array of `{ session_id, job_role, interview_type, created_at, completed_at }`

---

### `GET /sessions/{session_id}`
Get full session detail: all turns with transcripts and the feedback report.

---

## 6. Data Models

### `sessions`
```sql
session_id      UUID          PRIMARY KEY
user_id         TEXT          NOT NULL
job_role        TEXT
interview_type  TEXT
user_profile    JSONB
created_at      TIMESTAMP     DEFAULT now()
completed_at    TIMESTAMP
```

### `turns`
```sql
turn_id         UUID          PRIMARY KEY
session_id      UUID          REFERENCES sessions(session_id)
turn_index      INTEGER
question_text   TEXT
transcript      TEXT
filler_count    INTEGER
filler_words    JSONB         -- e.g. {"um": 3, "like": 5, "you know": 2}
pause_count     INTEGER
wpm             FLOAT         -- stored but excluded from LLM feedback
created_at      TIMESTAMP     DEFAULT now()
```

### `feedback`
```sql
feedback_id     UUID          PRIMARY KEY
session_id      UUID          REFERENCES sessions(session_id) UNIQUE
report          TEXT          -- LLM-generated markdown
created_at      TIMESTAMP     DEFAULT now()
```

---

## 7. In-Memory Session Store

Active sessions live in a module-level dict during an interview:

```python
{
  "session_id": {
    "user_profile": { ... },
    "turns": [
      {
        "turn_index": 0,
        "question_text": "...",
        "transcript": "...",
        "filler_words": {"um": 2},
        "pause_count": 3,
        "wpm": 142.0
      }
    ]
  }
}
```

This is cleared from memory after `POST /end` persists the session to Cloud SQL.

---

## 8. Speech Analytics Pipeline

Runs as a FastAPI `BackgroundTask` after each turn's transcript is returned.

**Input:** Whisper `verbose_json` response (includes word-level timestamps) + audio duration

**Metrics extracted:**

| Metric | Method | Sent to LLM |
|---|---|---|
| Transcript | Whisper output | Yes |
| Filler words | Regex scan against keyword list | Yes |
| Pause count | Word timestamp gaps > 1.5s threshold | Yes |
| WPM | `word_count / audio_duration * 60` | **No** — stored only |

**Filler word list (v1):** `um, uh, like, you know, so, basically, literally, actually, right, kind of, sort of`

---

## 9. LLM Integration

### Follow-up question generation (during interview)
- **Input:** conversation history (question/transcript pairs) + job role
- **Model:** Gemini 2.0 Flash
- **Note:** This is called by the frontend/orchestration layer, not directly by the speech pipeline. The speech pipeline only provides the transcript.

### Feedback generation (end of interview)
- **Model:** Gemini 2.0 Flash
- **Payload sent:**

```
You are an expert, inclusive interview coach.

User profile:
- Communication challenges: {challenges}
- Experience level: {experience_level}
- Goals: {goals}

Do not penalize the user for documented communication differences.
Provide constructive, specific, actionable feedback.

Interview context:
- Job role: {job_role}
- Interview type: {interview_type}

Turns:
[
  {
    "question": "...",
    "transcript": "...",
    "filler_words": {"um": 3, "like": 2},
    "pause_count": 4
  },
  ...
]

Generate a structured feedback report covering:
1. Content quality and relevance of answers
2. Communication clarity
3. Use of filler words (contextualized, not punitive)
4. Strengths observed
5. Specific areas for improvement with actionable suggestions
```

---

## 10. Error Handling

| Scenario | Handling |
|---|---|
| Whisper API failure | Return HTTP 502 with `{"error": "transcription_failed"}`; turn not stored |
| Background analytics crash | Log error, store turn with null metrics; session continues |
| Gemini API failure on `/end` | Return HTTP 502; session marked incomplete in DB; user can retry `/end` |
| Session not found | Return HTTP 404 |
| Audio format unsupported | Validate before sending to Whisper; return HTTP 400 |

Analytics failures are non-fatal by design — a turn with a missing metric is better than a failed session.

---

## 11. Out of Scope (This Spec)

- User authentication and JWT handling (assumed provided by auth layer; `user_id` passed by client)
- Vision/computer vision module (Harshit's domain)
- Frontend implementation
- LLM-side question generation logic (orchestration layer, separate spec)
- Deployment / Cloud Run configuration
- WCAG accessibility features
