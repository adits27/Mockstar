# ADR 001 — Two-Layer State: In-Memory Store + Cloud SQL

**Status:** Accepted  
**Date:** 2026-05

---

## Context

MockStar needs to maintain state across multiple HTTP requests within a single interview session — tracking turns, transcripts, CV results, and pending background task counts. Options considered:

1. **Write every update to the database** as it arrives
2. **Hold all in-flight state in memory**, then persist once at session end
3. **Use an external cache** (Redis, Memcached)

## Decision

Use a **module-level Python dict** (`app/store/session_store.py`) for all in-flight session state. At session end (`POST /sessions/{id}/end`), the complete session is written to Cloud SQL in a single atomic commit via `persist_completed_session`. The database is only ever read for completed sessions.

## Consequences

**Benefits:**
- Background tasks (Whisper transcription, CV analysis) can update the store without database round-trips, keeping per-turn response latency near zero
- A single atomic write at session end avoids partial-state consistency problems — either the full session persists, or none of it does
- No external infrastructure dependency; the store is just Python

**Trade-offs:**
- In-flight sessions are lost on server restart — acceptable given the interactive, real-time nature of a mock interview
- The store is not shared across multiple server instances; horizontal scaling requires session-affinity or migration to a shared cache
- A 2-hour TTL and 5-minute cleanup sweep (`main.py`) are required to prevent unbounded memory growth

**Source files:** `app/store/session_store.py`, `app/services/persistence.py`, `app/main.py`
