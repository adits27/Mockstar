"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { DualRecorder, type RecordingResult } from "@/lib/mediaRecorder"

export function useMediaRecorder() {
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const recorderRef = useRef<DualRecorder | null>(null)

  useEffect(() => {
    navigator.mediaDevices
      .getUserMedia({ audio: true, video: { width: 1280, height: 720, facingMode: "user" } })
      .then(setStream)
      .catch(() => {
        // Fall back to audio-only
        navigator.mediaDevices
          .getUserMedia({ audio: true })
          .then(setStream)
          .catch(() => setError("Camera and microphone access is required for the interview."))
      })

    return () => {
      stream?.getTracks().forEach((t) => t.stop())
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const startRecording = useCallback(() => {
    if (!stream) return
    recorderRef.current = new DualRecorder(stream)
    recorderRef.current.start()
    setIsRecording(true)
  }, [stream])

  const stopRecording = useCallback((): Promise<RecordingResult> => {
    return new Promise((resolve, reject) => {
      if (!recorderRef.current) return reject(new Error("No active recording"))
      recorderRef.current.stop().then((result) => {
        setIsRecording(false)
        resolve(result)
      })
    })
  }, [])

  return { stream, isRecording, startRecording, stopRecording, error }
}
