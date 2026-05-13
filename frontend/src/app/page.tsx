"use client"

import { signIn, useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useEffect } from "react"
import { Button } from "@/components/ui/Button"

export default function Landing() {
  const { data: session, status } = useSession()
  const router = useRouter()

  useEffect(() => {
    if (session) router.replace("/dashboard")
  }, [session, router])

  if (status === "loading") return null

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Nav */}
      <header className="max-w-6xl mx-auto w-full px-4 py-5 flex items-center justify-between">
        <span className="font-semibold text-slate-900 text-lg tracking-tight">MockStar</span>
        <Button variant="secondary" size="sm" onClick={() => signIn("google")}>
          Sign in
        </Button>
      </header>

      {/* Hero */}
      <main className="flex-1 flex items-center justify-center px-4 py-20">
        <div className="max-w-2xl mx-auto text-center">
          <span className="inline-block px-3 py-1 text-xs font-medium bg-slate-100 text-slate-600 rounded-full mb-6">
            AI-powered interview coaching
          </span>
          <h1 className="text-5xl font-bold text-slate-900 leading-tight mb-6">
            Practise interviews.
            <br />
            <span className="text-slate-400">Get better, faster.</span>
          </h1>
          <p className="text-lg text-slate-500 mb-10 leading-relaxed">
            MockStar simulates real interviews, analyses your speech and body language, and delivers
            personalised feedback grounded in your own resume and experience.
          </p>
          <Button size="lg" onClick={() => signIn("google")}>
            Start with Google
          </Button>
        </div>
      </main>

      {/* Feature row */}
      <section className="border-t border-slate-100 bg-slate-50">
        <div className="max-w-6xl mx-auto px-4 py-14 grid grid-cols-1 sm:grid-cols-3 gap-8">
          {[
            {
              title: "Resume-aware questions",
              body: "Upload your CV and the AI tailors every question to your actual background.",
            },
            {
              title: "Audio + video scoring",
              body: "Filler words, pacing, and eye contact are all tracked and scored objectively.",
            },
            {
              title: "Actionable feedback",
              body: "Get specific story suggestions from your resume to strengthen your answers.",
            },
          ].map((f) => (
            <div key={f.title}>
              <h3 className="font-semibold text-slate-800 mb-2">{f.title}</h3>
              <p className="text-sm text-slate-500 leading-relaxed">{f.body}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
