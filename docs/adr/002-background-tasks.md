# ADR 002 — Non-Blocking Turns via Background Tasks

**Status:** Accepted  
**Date:** 2026-05

---

## Context

When a candidate submits an answer, the server must:
1. Transcribe audio (Whisper API — network call, typically 2–10 s)
2. Analyse video frames for gaze tracking (CPU-bound, scales with clip length)
3. Run speech analytics (fast, local)

If these run synchronously, the HTTP response is blocked for 5–15 seconds per turn — an unacceptable UX. The candidate would be stuck on a loading screen between every answer.

## Decision

Transcription and analytics are dispatched as **FastAPI `BackgroundTask`s** immediately after the turn stub is created in the session store. The `POST /sessions/{id}/turns` endpoint returns a `TurnResponse` immediately (with `transcript: ""`), before any of those tasks complete.

At session end, `POST /sessions/{id}/end` polls the in-memory store's `pending_count` field — waiting up to 30 seconds — to ensure all background tasks have finished before generating feedback.

## Consequences

**Benefits:**
- Per-turn HTTP response is immediate; the candidate receives their `turn_id` in milliseconds
- Whisper and OpenCV run in parallel with the candidate reading their next question, effectively hiding their latency
- The 30-second cap at session end acts as a safety valve without blocking the per-turn flow

**Trade-offs:**
- Transcripts are not available on the `TurnResponse` — clients must fetch them later (via `GET /sessions/{id}`) if they need them during the session
- If the server crashes mid-session, in-progress background tasks are silently lost
- The 30-second polling loop at session end (`asyncio.sleep(0.25)`) is a simple but blunt mechanism — a proper task queue (Celery, ARQ) would be more robust at scale

**Source files:** `app/routers/turns.py`, `app/store/session_store.py`
