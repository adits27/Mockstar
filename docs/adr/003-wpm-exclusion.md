# ADR 003 — WPM Excluded from Gemini Feedback Prompt

**Status:** Accepted  
**Date:** 2026-05

---

## Context

Words-per-minute (WPM) is calculated per turn from Whisper's word-level timestamps and stored in the `turns` table. It was initially considered as an input signal for the Gemini feedback prompt — used to flag candidates who speak too slowly or too quickly.

## Decision

**WPM is stored in the database but never passed to the Gemini feedback prompt.**

The `build_feedback_prompt` function in `app/services/feedback.py` includes `filler_words` and `pause_count` per turn but deliberately omits `wpm`.

## Consequences

**Benefits:**
- Prevents penalising non-native English speakers, who statistically speak at lower WPM than native speakers
- Prevents penalising candidates with documented communication differences (stammer, cluttering, etc.)
- Speaking pace has weak predictive validity for actual job performance compared to content quality
- Gemini has no reliable calibration for what constitutes an "appropriate" WPM for a given role or domain

**Trade-offs:**
- Genuinely incoherent pace (e.g., 20 WPM) that would genuinely impede comprehension cannot be flagged by the model
- WPM data is captured and stored — a future opt-in feedback mode could surface it for candidates who explicitly want pace coaching

**Source files:** `app/services/feedback.py:build_feedback_prompt`, `app/models/db.py:DBTurn.wpm`
