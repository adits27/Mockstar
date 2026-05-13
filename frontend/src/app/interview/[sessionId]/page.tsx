"use client"

import { useParams, useRouter, useSearchParams } from "next/navigation"
import { useEffect, useRef } from "react"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"
import { useInterview } from "@/hooks/useInterview"
import { useMediaRecorder } from "@/hooks/useMediaRecorder"

export default function ActiveInterview() {
  const params = useParams()
  const searchParams = useSearchParams()
  const router = useRouter()
  const sessionId = params.sessionId as string
  const numQuestions = parseInt(searchParams.get("n") ?? "5", 10)

  const { state, isLast, loadNextQuestion, startRecording, submitAnswer, nextQuestion, finish } =
    useInterview(sessionId, numQuestions)

  const {
    stream,
    isRecording,
    startRecording: startMedia,
    stopRecording,
    error: mediaError,
  } = useMediaRecorder()

  const videoRef = useRef<HTMLVideoElement>(null)

  // Load first question on mount
  useEffect(() => {
    loadNextQuestion()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Bind camera stream to the video preview element
  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream
    }
  }, [stream])

  // Redirect when interview ends
  useEffect(() => {
    if (state.phase === "done") {
      router.replace(`/sessions/${sessionId}/feedback`)
    }
  }, [state.phase, sessionId, router])

  async function handleRecord() {
    startRecording()
    startMedia()
  }

  async function handleStop() {
    const result = await stopRecording()
    await submitAnswer(result.audioBlob, result.videoBlob)
  }

  const progress = `Question ${state.questionIndex + 1} of ${numQuestions}`

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top bar */}
      <header className="bg-white border-b border-slate-100 px-4 py-3 flex items-center justify-between">
        <span className="font-semibold text-slate-900">MockStar</span>
        <span className="text-sm text-slate-400">{progress}</span>
      </header>

      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-8 grid md:grid-cols-2 gap-6 items-start">
        {/* Left: question + transcript */}
        <div className="space-y-4">
          <Card>
            {state.phase === "loading" ? (
              <div className="space-y-2 animate-pulse">
                <div className="h-4 bg-slate-100 rounded w-3/4" />
                <div className="h-4 bg-slate-100 rounded w-1/2" />
              </div>
            ) : (
              <>
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">
                  Question
                </p>
                <p className="text-lg font-medium text-slate-800 leading-snug">{state.question}</p>
              </>
            )}
          </Card>

          {state.transcript && (
            <Card>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">
                Your answer
              </p>
              <p className="text-sm text-slate-700 leading-relaxed">{state.transcript}</p>
            </Card>
          )}

          {state.error && (
            <p className="text-sm text-red-600 bg-red-50 rounded-xl px-4 py-3">{state.error}</p>
          )}

          {/* Controls */}
          <div className="flex gap-3">
            {(state.phase === "ready" || state.phase === "loading") && (
              <Button
                className="flex-1"
                onClick={handleRecord}
                disabled={state.phase === "loading" || !stream}
              >
                <span className="w-2 h-2 rounded-full bg-red-500" />
                Record answer
              </Button>
            )}

            {state.phase === "recording" && (
              <Button className="flex-1" variant="danger" onClick={handleStop}>
                <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
                Stop recording
              </Button>
            )}

            {state.phase === "processing" && (
              <Button className="flex-1" loading disabled>
                Transcribing…
              </Button>
            )}

            {state.phase === "answered" && (
              <>
                {isLast ? (
                  <Button className="flex-1" onClick={finish}>
                    End interview & get feedback
                  </Button>
                ) : (
                  <Button className="flex-1" onClick={nextQuestion}>
                    Next question →
                  </Button>
                )}
              </>
            )}

            {state.phase === "ending" && (
              <Button className="flex-1" loading disabled>
                Generating feedback…
              </Button>
            )}
          </div>
        </div>

        {/* Right: video preview */}
        <div className="space-y-4">
          <Card padded={false} className="overflow-hidden aspect-video bg-slate-900 relative">
            {mediaError ? (
              <div className="absolute inset-0 flex items-center justify-center p-6">
                <p className="text-white/60 text-sm text-center">{mediaError}</p>
              </div>
            ) : (
              <video
                ref={videoRef}
                autoPlay
                muted
                playsInline
                className="w-full h-full object-cover scale-x-[-1]"
              />
            )}
            {isRecording && (
              <div className="absolute top-3 right-3 flex items-center gap-1.5 bg-black/50 backdrop-blur rounded-full px-2.5 py-1">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                <span className="text-white text-xs font-medium">REC</span>
              </div>
            )}
          </Card>
          <p className="text-xs text-slate-400 text-center">
            Your camera feed is not recorded to the server until you stop recording.
          </p>
        </div>
      </main>
    </div>
  )
}
