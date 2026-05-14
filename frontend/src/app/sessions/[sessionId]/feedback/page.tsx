"use client"

import { useParams, useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import ReactMarkdown from "react-markdown"
import Link from "next/link"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"
import { PageShell } from "@/components/layout/PageShell"
import { getSession } from "@/lib/api"
import type { SessionDetail } from "@/types"

const SCORE_META: Record<string, { label: string; description: string }> = {
  answer_relevance: {
    label: "Content Quality & Relevance",
    description: "How directly and thoroughly your answers addressed each question.",
  },
  experience_articulation: {
    label: "Experience Articulation",
    description: "How clearly you drew on relevant past experiences and concrete examples.",
  },
  industry_fit: {
    label: "Industry Fit",
    description: "How well you demonstrated knowledge of the role and industry.",
  },
  clarity_and_structure: {
    label: "Communication Clarity",
    description: "How organized, concise, and easy to follow your responses were.",
  },
  filler_word_usage: {
    label: "Filler Word Usage",
    description: "How rarely you used filler words such as 'um', 'uh', or 'like'.",
  },
  eye_contact_and_presence: {
    label: "Eye Contact & Presence",
    description: "How engaged and confident you appeared on camera.",
  },
}

function scoreColor(score: number) {
  const pct = (score / 10) * 100
  if (pct >= 75) return "text-emerald-600"
  if (pct >= 50) return "text-amber-500"
  return "text-red-500"
}

function barColor(score: number) {
  const pct = (score / 10) * 100
  if (pct >= 75) return "bg-emerald-500"
  if (pct >= 50) return "bg-amber-400"
  return "bg-red-400"
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
          <div className="h-8 bg-white/60 rounded-xl w-1/3" />
          <div className="h-40 bg-white/60 rounded-2xl" />
          <div className="h-64 bg-white/60 rounded-2xl" />
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
    ? Object.entries(scores).filter(
        ([k]) => k !== "overall" && scores[k as keyof typeof scores] !== null,
      )
    : []

  return (
    <PageShell>
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Interview feedback</h1>
            <p className="text-slate-500 text-sm mt-1 capitalize">
              {session.job_role} · {session.interview_type}
            </p>
          </div>
          <Link href="/interview/new">
            <Button variant="secondary">Practice again</Button>
          </Link>
        </div>

        {/* ── 1. Overall Performance ──────────────────────────── */}
        {scores?.overall && (
          <Card>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
              Overall Performance
            </p>
            <div className="flex items-center gap-6">
              <div className={`text-6xl font-bold tabular-nums ${scoreColor(scores.overall)}`}>
                {scores.overall.toFixed(1)}
                <span className="text-2xl text-slate-300 font-normal">/10</span>
              </div>
              <div className="flex-1 space-y-2">
                <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${barColor(scores.overall)}`}
                    style={{ width: `${(scores.overall / 10) * 100}%` }}
                  />
                </div>
                {session.confidence_label && (
                  <span
                    className={`inline-block text-xs font-medium px-2.5 py-1 rounded-full ${
                      session.confidence_label === "High"
                        ? "bg-emerald-100 text-emerald-700"
                        : session.confidence_label === "Medium"
                          ? "bg-amber-100 text-amber-700"
                          : "bg-red-100 text-red-700"
                    }`}
                  >
                    Presence: {session.confidence_label}
                  </span>
                )}
              </div>
            </div>
          </Card>
        )}

        {/* ── 2. Score Breakdown ──────────────────────────────── */}
        {(scores?.overall || scoreEntries.length > 0) && (
          <div className="space-y-3">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-1">
              Score Breakdown
            </p>

            {scores?.overall && (
              <Card>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-semibold text-slate-700">Overall Score</p>
                  <span className={`text-lg font-bold tabular-nums ${scoreColor(scores.overall)}`}>
                    {scores.overall.toFixed(1)}
                    <span className="text-sm font-normal text-slate-300">/10</span>
                  </span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden mb-2">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${barColor(scores.overall)}`}
                    style={{ width: `${(scores.overall / 10) * 100}%` }}
                  />
                </div>
                <p className="text-xs text-slate-400">Your weighted score across all dimensions.</p>
              </Card>
            )}

            {scoreEntries.map(([key, value]) => {
              const meta = SCORE_META[key] ?? { label: key, description: "" }
              return (
                <Card key={key}>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-semibold text-slate-700">{meta.label}</p>
                    <span className={`text-lg font-bold tabular-nums ${scoreColor(value as number)}`}>
                      {(value as number).toFixed(1)}
                      <span className="text-sm font-normal text-slate-300">/10</span>
                    </span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden mb-2">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${barColor(value as number)}`}
                      style={{ width: `${((value as number) / 10) * 100}%` }}
                    />
                  </div>
                  {meta.description && (
                    <p className="text-xs text-slate-400">{meta.description}</p>
                  )}
                </Card>
              )
            })}
          </div>
        )}

        {/* ── 4. Actionable Insights ──────────────────────────── */}
        {session.observations && session.observations.length > 0 && (
          <Card>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
              Actionable Insights
            </p>
            <ul className="space-y-3">
              {session.observations.map((obs, i) => (
                <li key={i} className="flex gap-3 items-start">
                  <span className="mt-0.5 shrink-0 text-lg leading-none">💡</span>
                  <p className="text-sm text-slate-700 leading-relaxed">{obs}</p>
                </li>
              ))}
            </ul>
          </Card>
        )}

        {/* ── 5. Detailed Feedback ────────────────────────────── */}
        {session.feedback && (
          <Card>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
              Detailed Feedback
            </p>
            <div className="prose prose-sm prose-slate max-w-none prose-headings:font-semibold prose-headings:text-slate-800 prose-p:text-slate-600 prose-li:text-slate-600">
              <ReactMarkdown>{session.feedback}</ReactMarkdown>
            </div>
          </Card>
        )}

        {/* ── 6. Question-by-Question Breakdown ──────────────── */}
        {session.turns && session.turns.length > 0 && (
          <Card>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
              Question-by-Question Breakdown
            </p>
            <div className="space-y-3">
              {session.turns.map((turn, i) => (
                <details key={i} open={i === 0} className="group">
                  <summary className="flex items-center justify-between cursor-pointer list-none rounded-xl px-4 py-3 bg-slate-50/80 hover:bg-violet-50/60 transition-colors">
                    <span className="text-sm font-medium text-slate-700">
                      Q{i + 1}. {turn.question_text}
                    </span>
                    <svg
                      className="w-4 h-4 text-slate-400 shrink-0 ml-3 transition-transform group-open:rotate-180"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                  </summary>

                  <div className="px-4 pt-3 pb-1 space-y-3">
                    {turn.transcript && (
                      <div>
                        <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                          Your answer
                        </p>
                        <p className="text-sm text-slate-600 leading-relaxed">{turn.transcript}</p>
                      </div>
                    )}

                    <div className="flex flex-wrap gap-2 pt-1">
                      {turn.pause_count > 0 && (
                        <span className="text-xs bg-amber-50 text-amber-700 border border-amber-100 rounded-full px-2.5 py-1">
                          {turn.pause_count} pause{turn.pause_count !== 1 ? "s" : ""}
                        </span>
                      )}
                      {turn.wpm !== null && (
                        <span className="text-xs bg-slate-50 text-slate-600 border border-slate-100 rounded-full px-2.5 py-1">
                          {turn.wpm} WPM
                        </span>
                      )}
                      {turn.filler_words &&
                        Object.entries(turn.filler_words).map(([word, count]) => (
                          <span
                            key={word}
                            className="text-xs bg-rose-50 text-rose-600 border border-rose-100 rounded-full px-2.5 py-1"
                          >
                            &quot;{word}&quot; ×{count}
                          </span>
                        ))}
                    </div>
                  </div>
                </details>
              ))}
            </div>
          </Card>
        )}
      </div>
    </PageShell>
  )
}
