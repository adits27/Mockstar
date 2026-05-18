# ADR 004 — Pause Detection Threshold of 1.5 Seconds

**Status:** Accepted  
**Date:** 2026-05

---

## Context

Pause detection uses the gap between consecutive Whisper word timestamps to identify hesitations. The core question is: what gap constitutes a meaningful pause versus a natural breath or clause boundary?

Options considered:
- **0.5 s** — captures micro-pauses, but produces high false-positive rates for natural speech rhythm
- **1.0 s** — borderline; still flags normal clause breaks in slower speakers
- **1.5 s** — clearly perceptible pause to a listener; unlikely to be a natural breath
- **2.0 s** — only catches very long hesitations; misses moderate disruptions

## Decision

Use a **1.5-second gap** between consecutive Whisper word timestamps as the pause threshold.

```python
# app/services/analytics.py:28
def detect_pauses(words: list[dict], threshold: float = 1.5) -> int:
    ...
    if words[i]["start"] - words[i - 1]["end"] > threshold
```

## Consequences

**Benefits:**
- 1.5 s is the approximate threshold at which listeners consistently perceive a disruption rather than a natural break (supported by speech communication research)
- Whisper word timestamps can have ±100–200 ms variance at word boundaries — a 1.5 s threshold provides adequate margin
- The threshold is a named parameter, making it easy to adjust per interview type or user preference in future

**Trade-offs:**
- Whisper occasionally mis-aligns timestamps near punctuation — a 1.5 s gap may occasionally be caused by a transcription artefact rather than a real pause
- The threshold is applied uniformly regardless of speaking rate — a naturally faster speaker's 1.5 s pause is more significant than a slower speaker's

**Source files:** `app/services/analytics.py:detect_pauses`
