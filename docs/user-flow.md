# User Flow Diagram

```mermaid
flowchart TD
    A([fa:fa-globe Landing Page /]) --> B{Signed in?}

    B -- No --> C[Sign in with Google OAuth]
    C --> D{Resume on file?}
    B -- Yes --> D

    D -- No --> E["Onboarding /onboarding\n─────────────────────\nStep 1 · Experience level\n         Communication challenges\n         Goals\nStep 2 · Resume upload PDF/DOCX"]
    E --> F

    D -- Yes --> F([Dashboard /dashboard\nAll completed sessions])

    F --> G["New Interview Setup /interview/new\n─────────────────────────────\nJob role · Company · Interview type\nNum questions · Job description"]
    G --> H[POST /sessions\nCreate session in memory]
    H --> I["Active Interview /interview/sessionId\n────────────────────────────────────\nLoad first question via Gemini"]

    I --> J["Record answer\naudio + video via MediaRecorder"]
    J --> K[POST /sessions/id/turns\nUpload audio + video]
    K --> L["Background tasks fire\n• Whisper transcription\n• Filler + pause analytics\n• OpenCV gaze analysis"]
    L --> M{Last question?}

    M -- No --> N[POST /sessions/id/next-question\nGemini generates follow-up]
    N --> J

    M -- Yes --> O[POST /sessions/id/end\nAggregate CV · Generate feedback\nPersist to Cloud SQL]
    O --> P(["Feedback /sessions/sessionId/feedback\n──────────────────────────────────\nOverall score · 6-dimension breakdown\nActionable insights · Turn-by-turn detail"])

    P --> F
    F --> Q([View past session\n/sessions/sessionId/feedback])
```

---

## Phase Summary

| Phase | Route | Key Events |
|---|---|---|
| Discovery | `/` | Features, FAQ, sign-in CTA |
| Authentication | Google OAuth | `sub` claim stored as `user_id` in JWT |
| Onboarding | `/onboarding` | Profile captured; resume uploaded and stored in `user_resumes` |
| Interview Setup | `/interview/new` | Session parameters collected; `POST /sessions` creates in-memory session |
| Active Interview | `/interview/[sessionId]` | `loading → ready → recording → processing → answered` (loops per question) → `ending → done` |
| Results | `/sessions/[sessionId]/feedback` | Scores, AI feedback, per-turn breakdown |
| History | `/dashboard` | All completed sessions listed as cards |

## Guards

- Unauthenticated users are redirected to `/` from any protected route via `frontend/src/proxy.ts`.
- Authenticated users without a resume are redirected to `/onboarding` from `/dashboard`.
- Raw audio and video are never persisted — processed in-memory and discarded after each turn.
