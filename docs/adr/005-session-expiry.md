# ADR 005 — Session TTL: 2-Hour Expiry with 5-Minute Cleanup Sweep

**Status:** Accepted  
**Date:** 2026-05

---

## Context

In-memory sessions must expire to prevent unbounded memory growth. Abandoned sessions (browser closed mid-interview, network failure, etc.) would otherwise persist indefinitely.

Two parameters require a decision:
1. **TTL** — how long an idle session is retained before eviction
2. **Cleanup interval** — how frequently the background sweep runs

## Decision

- **TTL: 2 hours** of inactivity before a session is eligible for eviction
- **Cleanup interval: every 5 minutes** — a background coroutine in `main.py` sweeps expired sessions on this schedule

A session's last-activity timestamp is updated on every write to the store (turn submission, transcript update, CV result). Expiry is based on inactivity, not absolute age.

## Consequences

**Benefits:**
- 2 hours comfortably covers the longest realistic interview session (7 questions + breaks + processing time)
- 5-minute cleanup granularity means memory is reclaimed within 5–7 minutes of a session expiring, without imposing significant CPU overhead
- Inactivity-based expiry means a candidate who pauses mid-interview to take a call is not unexpectedly evicted

**Trade-offs:**
- Sessions abandoned at the very start (before any turns) are held for 2 hours unnecessarily — a shorter TTL for sessions with zero turns would be a reasonable optimisation
- The cleanup sweep iterates the full session dict — at scale with thousands of concurrent sessions, a TTL-indexed structure (e.g., sorted set) would be more efficient
- No notification is sent to the client when a session expires — the next API call returns a `404`, which the frontend must handle gracefully

**Source files:** `app/store/session_store.py`, `app/main.py`
