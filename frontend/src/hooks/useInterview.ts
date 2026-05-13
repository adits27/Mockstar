"use client"

import { useCallback, useState } from "react"
import * as api from "@/lib/api"
import type { FeedbackResponse } from "@/types"

type Phase =
  | "loading"
  | "ready"
  | "recording"
  | "processing"
  | "answered"
  | "ending"
  | "done"

interface InterviewState {
  phase: Phase
  question: string
  questionIndex: number
  transcript: string
  feedback: FeedbackResponse | null
  error: string | null
}

export function useInterview(sessionId: string, numQuestions: number) {
  const [state, setState] = useState<InterviewState>({
    phase: "loading",
    question: "",
    questionIndex: 0,
    transcript: "",
    feedback: null,
    error: null,
  })

  const isLast = state.questionIndex + 1 >= numQuestions

  const loadNextQuestion = useCallback(async () => {
    setState((s) => ({ ...s, phase: "loading", error: null }))
    try {
      const { question } = await api.nextQuestion(sessionId)
      setState((s) => ({ ...s, phase: "ready", question }))
    } catch (e) {
      setState((s) => ({ ...s, error: (e as Error).message, phase: "ready" }))
    }
  }, [sessionId])

  const startRecording = useCallback(() => {
    setState((s) => ({ ...s, phase: "recording" }))
  }, [])

  const submitAnswer = useCallback(
    async (audioBlob: Blob, videoBlob: Blob | null) => {
      setState((s) => ({ ...s, phase: "processing" }))
      try {
        const { transcript } = await api.postTurn(
          sessionId,
          state.question,
          audioBlob,
          videoBlob,
        )
        setState((s) => ({ ...s, phase: "answered", transcript }))
      } catch (e) {
        setState((s) => ({ ...s, error: (e as Error).message, phase: "answered" }))
      }
    },
    [sessionId, state.question],
  )

  const nextQuestion = useCallback(async () => {
    setState((s) => ({
      ...s,
      questionIndex: s.questionIndex + 1,
      transcript: "",
    }))
    await loadNextQuestion()
  }, [loadNextQuestion])

  const finish = useCallback(async () => {
    setState((s) => ({ ...s, phase: "ending" }))
    try {
      const feedback = await api.endInterview(sessionId)
      setState((s) => ({ ...s, phase: "done", feedback }))
    } catch (e) {
      setState((s) => ({ ...s, error: (e as Error).message, phase: "answered" }))
    }
  }, [sessionId])

  return { state, isLast, loadNextQuestion, startRecording, submitAnswer, nextQuestion, finish }
}
