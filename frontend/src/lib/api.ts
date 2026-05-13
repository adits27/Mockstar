import type {
  CreateSessionRequest,
  FeedbackResponse,
  NextQuestionResponse,
  ResumeResponse,
  SessionDetail,
  SessionSummary,
  TurnResponse,
} from "@/types"

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, init)
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`${res.status} ${path}: ${body}`)
  }
  return res.json()
}

export function createSession(body: CreateSessionRequest) {
  return request<{ session_id: string }>("/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
}

export function getSessions(userId: string) {
  return request<SessionSummary[]>(`/sessions?user_id=${encodeURIComponent(userId)}`)
}

export function getSession(sessionId: string) {
  return request<SessionDetail>(`/sessions/${sessionId}`)
}

export function nextQuestion(sessionId: string) {
  return request<NextQuestionResponse>(`/sessions/${sessionId}/next-question`, {
    method: "POST",
  })
}

export function postTurn(
  sessionId: string,
  questionText: string,
  audioBlob: Blob,
  videoBlob: Blob | null,
) {
  const form = new FormData()
  form.append("question_text", questionText)
  form.append("audio", audioBlob, "audio.webm")
  if (videoBlob) form.append("video", videoBlob, "video.webm")

  return request<TurnResponse>(`/sessions/${sessionId}/turns`, {
    method: "POST",
    body: form,
    // Do NOT set Content-Type — browser sets it with the multipart boundary
  })
}

export function endInterview(sessionId: string) {
  return request<FeedbackResponse>(`/sessions/${sessionId}/end`, { method: "POST" })
}

export function uploadResume(userId: string, file: File) {
  const form = new FormData()
  form.append("file", file)
  return request<{ message: string; char_count: number }>(`/users/${userId}/resume`, {
    method: "POST",
    body: form,
  })
}

export function getResume(userId: string) {
  return request<ResumeResponse>(`/users/${userId}/resume`)
}

export function extractDocumentText(userId: string, file: File) {
  const form = new FormData()
  form.append("file", file)
  return request<{ text: string }>(`/users/${userId}/extract-text`, {
    method: "POST",
    body: form,
  })
}
