"use client"

import { useSession } from "next-auth/react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"
import { PageShell } from "@/components/layout/PageShell"
import { getResume, getSessions } from "@/lib/api"
import type { SessionSummary } from "@/types"

function scoreColor(score: number | null) {
  if (score === null) return "text-slate-400"
  if (score >= 8) return "text-emerald-600"
  if (score >= 6) return "text-amber-600"
  return "text-red-500"
}

export default function Dashboard() {
  const { data: session } = useSession()
  const router = useRouter()
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!session?.user.id) return
    ;(async () => {
      try {
        await getResume(session.user.id)
      } catch {
        router.replace("/onboarding")
        return
      }
      const data = await getSessions(session.user.id)
      setSessions(data)
      setLoading(false)
    })()
  }, [session, router])

  return (
    <PageShell>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">My Practice</h1>
          <p className="text-slate-500 text-sm mt-1">
            {sessions.length === 0 && !loading
              ? "No completed interviews yet."
              : `${sessions.length} completed`}
          </p>
        </div>
        <Link href="/interview/new">
          <Button>New interview</Button>
        </Link>
      </div>

      {loading && (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-32 bg-slate-100 rounded-2xl animate-pulse" />
          ))}
        </div>
      )}

      {!loading && sessions.length === 0 && (
        <Card className="text-center py-16">
          <p className="text-slate-400 mb-6">Start your first practice interview to see results here.</p>
          <Link href="/interview/new">
            <Button>Begin practicing</Button>
          </Link>
        </Card>
      )}

      {!loading && sessions.length > 0 && (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {sessions.map((s) => (
            <Link key={s.session_id} href={`/sessions/${s.session_id}/feedback`}>
              <Card className="hover:shadow-md transition-shadow cursor-pointer h-full flex flex-col">
                <div className="flex items-start justify-between mb-2">
                  <div className="min-w-0 pr-3">
                    <p className="font-semibold text-slate-800 leading-tight">{s.job_role}</p>
                    <p className="text-sm text-slate-500 mt-0.5 truncate">{s.company_name || "—"}</p>
                    <p className="text-xs text-slate-400 mt-1 capitalize">{s.interview_type}</p>
                  </div>
                  {s.overall_score !== null && (
                    <span className={`text-xl font-bold shrink-0 ${scoreColor(s.overall_score)}`}>
                      {s.overall_score.toFixed(1)}
                      <span className="text-sm font-normal text-slate-400">/10</span>
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400 mt-auto pt-3 border-t border-slate-100">
                  {new Date(s.completed_at ?? s.created_at).toLocaleDateString("en-GB", {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                  })}{" · "}{new Date(s.completed_at ?? s.created_at).toLocaleTimeString("en-GB", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </PageShell>
  )
}
