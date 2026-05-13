"use client"

import { useParams, useRouter, useSearchParams } from "next/navigation"
import { useEffect, useRef } from "react"
import Image from "next/image"
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
    <div className="min-h-screen flex flex-col">
      {/* Top bar */}
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur shadow-sm border-b border-slate-200/60">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <div className="w-[118px] h-[30px] relative overflow-hidden rounded-md">
          <Image
            src="/logos/mockstar_logo.png"
            alt="MockStar"
            fill
            style={{ objectFit: "cover", objectPosition: "center 50%" }}
            priority
          />
        </div>
        <span className="text-sm text-slate-400">{progress}</span>
        </div>
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
              <div className="flex-1 space-y-3">
                <div className="flex items-end justify-center gap-1 h-9">
                  <span className="w-1.5 rounded-full bg-violet-500 voice-bar-1" style={{ height: 6 }} />
                  <span className="w-1.5 rounded-full bg-violet-400 voice-bar-2" style={{ height: 12 }} />
                  <span className="w-1.5 rounded-full bg-violet-500 voice-bar-3" style={{ height: 20 }} />
                  <span className="w-1.5 rounded-full bg-violet-400 voice-bar-4" style={{ height: 10 }} />
                  <span className="w-1.5 rounded-full bg-violet-500 voice-bar-5" style={{ height: 16 }} />
                  <span className="ml-2 text-xs text-slate-500 self-center">Listening…</span>
                </div>
                <Button className="w-full" variant="danger" onClick={handleStop}>
                  <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
                  Stop recording
                </Button>
              </div>
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
