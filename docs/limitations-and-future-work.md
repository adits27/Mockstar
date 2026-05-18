---
output:
  html_document: default
  pdf_document: default
---

# Limitations & Future Work

This document distinguishes between features that are **fully implemented**, features that are **visible in the UI but not yet wired to the backend**, and features planned for **future development**.

---

## Currently Implemented

The following are fully functional end-to-end:

- Google OAuth authentication
- Resume upload, storage, and use in Gemini feedback
- Audio recording and Whisper transcription per turn
- Filler word detection and pause counting from word-level timestamps
- OpenCV gaze tracking and CV confidence scoring (0–100)
- Gemini-generated follow-up questions and structured feedback
- Session persistence to Cloud SQL at interview end
- Dashboard with full session history and per-session feedback pages
- Job description upload and paste (used in Gemini prompt for relevance scoring)

---

## UI-Only Features (Not Yet Backend-Implemented)

The following are visible and interactive in the UI but are not currently wired to the backend. They represent the next layer of implementation work.

### User Profile Fields (Experience Level, Communication Challenges, Goals)

The onboarding flow collects experience level, communication challenges (e.g. stammer, non-native English speaker, ADHD), and interview goals. However, the interview setup page currently passes `user_profile: {}` when creating a session — none of these values are sent to the backend or included in the Gemini prompt.

The backend schema and Gemini prompt are already built to receive and use this data (including the explicit non-penalisation instruction for documented communication differences). Wiring the frontend to pass it through is the remaining step.

### LinkedIn, GitHub, and Portfolio URL Fields

The onboarding step 2 collects optional LinkedIn, GitHub, and portfolio URLs. These are stored in component state but not submitted to any endpoint — they are discarded when the user completes onboarding.

The intended use is to surface relevant public work in Gemini's coaching feedback (e.g. referencing a GitHub project when evaluating a technical answer). This requires a backend endpoint to store the URLs per user and a change to the feedback prompt to incorporate them.

### Pricing Tiers

The `/pricing` page displays Free, Pro, and Teams tiers with feature breakdowns. All tiers are currently marked "Coming Soon" — no subscription, payment, or access-gating logic exists in the backend.

---

## Known Technical Limitations

### Scoring Split Not Hardcoded

Until now, the overall interview score has been a weighted average determined by Gemini rather than a fixed formula. The intended split — **70% content and delivery, 30% presence** — is being implemented as an explicit weighting in the Gemini feedback prompt, replacing the model's implicit judgement.

### In-Memory Session Store

Active sessions live in a module-level Python dict. This means:
- Sessions are lost if the backend restarts mid-interview
- The server cannot scale horizontally without session-affinity routing or migration to a shared store (e.g. Redis)

For a single-instance deployment this is acceptable, but it is a ceiling on reliability and scale.

### OpenCV Haar Cascade Accuracy

The CV pipeline uses OpenCV's Haar cascade classifiers for face and eye detection. These are fast and require no GPU, but are less accurate than modern deep learning alternatives (e.g. MediaPipe Face Mesh) — particularly under poor lighting, with glasses, or for faces at the edges of the frame. A misdetected face results in a `no_face` gaze classification, which reduces the face visibility score.

### No API Authentication

The FastAPI backend has no authentication layer — any client that knows the base URL can call any endpoint. For a production deployment serving real users, route-level auth (e.g. verifying a NextAuth JWT on the backend) would be required.

### Blink Detection Unreliable

The `blink_count` field in `CVMetrics` is stored but not used in scoring. At the 100 ms sampling interval, a blink (100–400 ms) may be captured as a single gaze-away frame or missed entirely, making the count unreliable.

---

## Planned Future Work

| Feature | Description |
|---|---|
| **Hardcoded 70/30 scoring split** | Explicitly weight content/delivery at 70% and presence at 30% in the Gemini prompt — in progress |
| **User profile wired end-to-end** | Pass experience level, communication challenges, and goals from onboarding through to the Gemini feedback prompt |
| **LinkedIn / GitHub integration** | Store and surface professional profile URLs as context in feedback generation |
| **Shared session store** | Replace the in-memory dict with Redis to support multi-instance deployment and survive restarts |
| **Backend API authentication** | Validate NextAuth session tokens on FastAPI routes |
| **MediaPipe gaze tracking** | Replace Haar cascade with MediaPipe Face Mesh for more robust eye contact detection across lighting conditions and face angles |
| **Subscription and access gating** | Implement the Free / Pro / Teams pricing model with Stripe and backend enforcement |
| **Session recording export** | Allow users to download a transcript and feedback report as a PDF after each session |
