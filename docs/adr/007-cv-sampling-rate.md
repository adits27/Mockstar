# ADR 007 — CV Pipeline Sampling Rate: 1 Frame per 100 ms

**Status:** Accepted  
**Date:** 2026-05

---

## Context

The computer vision pipeline (`app/services/cv/analyzer.py`) processes video by extracting and analysing individual frames. The core trade-off is between sampling granularity and processing cost:

- **Higher rate (e.g., every 33 ms / ~30 fps)** — fine-grained gaze timeline, captures rapid gaze shifts, but CPU cost scales linearly with video length and could make session end latency unacceptable
- **Lower rate (e.g., every 500 ms)** — fast processing, but misses short gaze-away events that are genuinely perceptible to an interviewer
- **100 ms (10 fps)** — captures all events lasting more than 100 ms; gaze-away events shorter than this are imperceptible to a human observer

## Decision

Sample **one frame every 100 milliseconds** (`_SAMPLE_INTERVAL_S = 0.1` in `app/services/cv/analyzer.py`).

## Consequences

**Benefits:**
- 10 fps is well above the perceptual threshold for eye contact assessment — a human interviewer cannot notice a 100 ms gaze break
- Processing a 60-second answer at 10 fps means ~600 frames: fast enough to complete well within the 30-second window at session end
- The 100 ms interval aligns naturally with the `avg_gaze_away_duration` metric — events shorter than the sample interval simply cannot be detected, which is the correct behaviour

**Trade-offs:**
- Blink detection (`blink_count` in `CVMetrics`) is unreliable at 10 fps — a blink (100–400 ms) may be captured as a gaze-away or missed entirely depending on frame timing
- Fast head movements or camera shake within a 100 ms window can cause a single "gaze-away" frame that does not represent a true gaze event — the confidence scorer's frequency thresholds (≤4/min for full marks) provide a buffer against isolated false positives

**Source files:** `app/services/cv/analyzer.py:_SAMPLE_INTERVAL_S`, `app/services/cv/gaze_tracker.py`
