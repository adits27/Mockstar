"use client"

import { useParams, useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import ReactMarkdown from "react-markdown"
import Link from "next/link"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"
import { ScoreCard } from "@/components/ui/ScoreCard"
import { PageShell } from "@/components/layout/PageShell"
import { getSession } from "@/lib/api"
import type { SessionDetail } from "@/types"

const SCORE_LABELS: Record<string, string> = {
  answer_relevance: "Answer Relevance",
  experience_articulation: "Experience Articulation",
  industry_fit: "Industry Fit",
  clarity_and_structure: "Clarity & Structure",
  filler_word_usage: "Filler Words",
  eye_contact_and_presence: "Eye Contact",
}

export default function FeedbackPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const router = useRouter()
  const [session, setSession] = useState<SessionDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getSession(sessionId)
      .then(setSession)
      .catch(() => setError("Could not load feedback. The session may still be processing."))
      .finally(() => setLoading(false))
  }, [sessionId])

  if (loading) {
    return (
      <PageShell>
        <div className="max-w-3xl mx-auto space-y-4 animate-pulse">
          <div className="h-8 bg-slate-100 rounded-xl w-1/3" />
          <div className="h-40 bg-slate-100 rounded-2xl" />
          <div className="h-64 bg-slate-100 rounded-2xl" />
        </div>
      </PageShell>
    )
  }

  if (error || !session) {
    return (
      <PageShell>
        <div className="max-w-3xl mx-auto text-center py-20">
          <p className="text-slate-500 mb-6">{error ?? "Session not found."}</p>
          <Button onClick={() => router.refresh()}>Retry</Button>
        </div>
      </PageShell>
    )
  }

  const scores = session.scores
  const scoreEntries = scores
    ? Object.entries(scores).filter(([k]) => k !== "overall" && scores[k as keyof typeof scores] !== null)
    : []

  return (
    <PageShell>
      <div className="max-w-3xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Interview feedback</h1>
            <p className="text-slate-500 text-sm mt-1 capitalize">
              {session.job_role} · {session.interview_type}
            </p>
          </div>
          <Link href="/interview/new">
            <Button variant="secondary">Practise again</Button>
          </Link>
        </div>

        {/* Overall score */}
        {scores?.overall && (
          <Card className="flex items-center gap-6">
            <div className="text-5xl font-bold text-slate-900">{scores.overall.toFixed(1)}</div>
            <div>
              <p className="text-sm text-slate-400 mb-1">Overall score</p>
              <div className="h-2 w-48 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-slate-900 rounded-full transition-all duration-700"
                  style={{ width: `${(scores.overall / 10) * 100}%` }}
                />
              </div>
            </div>
          </Card>
        )}

        {/* Score breakdown */}
        {scoreEntries.length > 0 && (
          <div>
            <h2 className="font-semibold text-slate-800 mb-4">Score breakdown</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {scoreEntries.map(([key, value]) => (
                <ScoreCard
                  key={key}
                  label={SCORE_LABELS[key] ?? key}
                  score={value as number}
                />
              ))}
            </div>
          </div>
        )}

        {/* CV confidence (if video was submitted) */}
        {session.confidence_score !== undefined && (
          <Card>
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold text-slate-800">Eye contact & presence</h2>
              <span
                className={`text-sm font-medium px-2.5 py-1 rounded-full ${
                  session.confidence_label === "High"
                    ? "bg-emerald-100 text-emerald-700"
                    : session.confidence_label === "Medium"
                      ? "bg-amber-100 text-amber-700"
                      : "bg-red-100 text-red-700"
                }`}
              >
                {session.confidence_label}
              </span>
            </div>
            <div className="h-2 bg-slate-100 rounded-full overflow-hidden mb-4">
              <div
                className="h-full bg-slate-900 rounded-full transition-all duration-700"
                style={{ width: `${session.confidence_score}%` }}
              />
            </div>
            {session.observations && session.observations.length > 0 && (
              <ul className="space-y-1.5">
                {session.observations.map((obs, i) => (
                  <li key={i} className="text-sm text-slate-600 flex gap-2">
                    <span className="text-slate-300 mt-0.5">–</span>
                    {obs}
                  </li>
                ))}
              </ul>
            )}
          </Card>
        )}

        {/* Feedback report */}
        {session.feedback && (
          <Card>
            <h2 className="font-semibold text-slate-800 mb-4">Detailed feedback</h2>
            <div className="prose prose-sm prose-slate max-w-none">
              <ReactMarkdown>{session.feedback}</ReactMarkdown>
            </div>
          </Card>
        )}
      </div>
    </PageShell>
  )
}
