"use client"

import { signIn, signOut, useSession } from "next-auth/react"
import Link from "next/link"
import Image from "next/image"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"
import { Footer } from "@/components/layout/Footer"

const HOW_IT_WORKS = [
  {
    step: "1",
    title: "Set up your interview",
    body: "Choose your role, company, and format. Optionally upload your CV — MockStar shapes every question around the experience you actually need to practice.",
  },
  {
    step: "2",
    title: "Answer with audio & video",
    body: "Respond to AI-generated questions out loud. Whisper transcribes your answers while the camera tracks your gaze and on-screen presence in real time.",
  },
  {
    step: "3",
    title: "Receive structured feedback",
    body: "Get a scored report across six dimensions, actionable insights, and a question-by-question breakdown you can use before the real interview.",
  },
]

const FEATURES = [
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-violet-600">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456Z" />
      </svg>
    ),
    title: "Tailored AI questions",
    body: "Gemini 2.5 Flash generates contextual follow-up questions grounded in your resume and live answers — not a generic question bank.",
  },
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-violet-600">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z" />
      </svg>
    ),
    title: "Speech analytics",
    body: "Whisper transcribes every answer and objectively tracks filler words, speaking pace, and unnatural pauses.",
  },
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-violet-600">
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
      </svg>
    ),
    title: "Gaze & presence scoring",
    body: "Computer vision monitors your eye contact and on-camera confidence across the entire session.",
  },
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-violet-600">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
      </svg>
    ),
    title: "Six-dimension scoring",
    body: "Every session is scored on relevance, articulation, industry fit, clarity, filler usage, and eye contact — so you know exactly where to improve.",
  },
]

const FAQ = [
  {
    q: "What makes MockStar different from static interview question lists?",
    a: "MockStar uses AI to generate follow-up questions in real time, tailored to your resume and what you actually said in your previous answer — not a predetermined list.",
  },
  {
    q: "Which interview formats are supported?",
    a: "Behavioral, technical, case study, and general. Questions adapt to your chosen format and target role throughout the session.",
  },
  {
    q: "Is my session data stored?",
    a: "Completed sessions are saved to your account so you can review feedback and track your progress over time. Nothing is shared with third parties.",
  },
]

export default function Landing() {
  const { data: session, status } = useSession()
  const isSignedIn = !!session

  if (status === "loading") return null

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Header ─────────────────────────────────────────── */}
      <header className="max-w-6xl mx-auto w-full px-4 py-5 flex items-center justify-between">
        <Link href="/" className="shrink-0">
          <div className="w-[118px] h-[30px] relative overflow-hidden rounded-md">
            <Image
              src="/logos/mockstar_logo.png"
              alt="MockStar"
              fill
              style={{ objectFit: "cover", objectPosition: "center 50%" }}
              priority
            />
          </div>
        </Link>
        <nav className="flex items-center gap-0.5">
          <Link
            href="/about"
            className="text-sm font-semibold text-slate-700 hover:text-violet-700 px-3.5 py-2 rounded-lg hover:bg-violet-50 transition-colors"
          >
            About
          </Link>
          <Link
            href="/pricing"
            className="flex items-center gap-1.5 text-sm font-semibold text-slate-700 hover:text-violet-700 px-3.5 py-2 rounded-lg hover:bg-violet-50 transition-colors"
          >
            Pricing
            <span className="text-[10px] font-semibold bg-violet-100 text-violet-600 rounded-full px-1.5 py-0.5 leading-none">
              Soon
            </span>
          </Link>
        </nav>

        <div className="flex items-center gap-3">
          {isSignedIn ? (
            <>
              <Link href="/dashboard">
                <Button variant="primary" size="sm">
                  My Practice →
                </Button>
              </Link>
              {session?.user.image && (
                <Image
                  src={session.user.image}
                  alt={session.user.name ?? "User"}
                  width={36}
                  height={36}
                  className="rounded-full ring-2 ring-violet-100"
                />
              )}
              <Button variant="ghost" size="sm" onClick={() => signOut({ callbackUrl: "/" })}>
                Sign out
              </Button>
            </>
          ) : (
            <Button variant="secondary" size="sm" onClick={() => signIn("google")}>
              Sign in
            </Button>
          )}
        </div>
      </header>

      {/* ── Hero ───────────────────────────────────────────── */}
      <section className="flex-1 flex items-center justify-center px-4 py-20">
        <div className="max-w-2xl mx-auto text-center">
          <span className="inline-block px-3 py-1 text-xs font-medium bg-violet-100 text-violet-700 rounded-full mb-6">
            AI-powered interview coaching
          </span>
          <h1 className="text-5xl font-bold text-slate-900 leading-tight mb-6">
            Mock Interviews That
            <br />
            <span className="text-violet-500">Match Your Background</span>
          </h1>
          <p className="text-lg text-slate-600 mb-4 leading-relaxed">
            MockStar turns your resume and target role into a tailored mock interview — with
            AI-generated follow-up questions, speech and presence analysis, and structured feedback
            you can act on.
          </p>
          <p className="text-sm text-slate-400 mb-10">
            Built for individual candidates. Extensible to career centers and training programs.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            {isSignedIn ? (
              <Link href="/dashboard">
                <Button size="lg">Go to My Practice →</Button>
              </Link>
            ) : (
              <Button size="lg" onClick={() => signIn("google")}>
                Start your first mock interview
              </Button>
            )}
            <a
              href="#how-it-works"
              className="text-sm text-slate-500 hover:text-slate-900 transition-colors"
            >
              See how it works ↓
            </a>
          </div>
        </div>
      </section>

      {/* ── How It Works ───────────────────────────────────── */}
      <section id="how-it-works" className="bg-white/40 backdrop-blur-sm border-y border-white/50">
        <div className="max-w-5xl mx-auto px-4 py-16">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider text-center mb-2">
            How MockStar Works
          </p>
          <h2 className="text-2xl font-bold text-slate-900 text-center mb-10">
            Practice interviews that match your background and target role
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {HOW_IT_WORKS.map((item) => (
              <Card key={item.step} className="flex gap-4 items-start">
                <div className="shrink-0 w-8 h-8 rounded-full bg-violet-100 text-violet-600 flex items-center justify-center font-bold text-sm">
                  {item.step}
                </div>
                <div>
                  <h3 className="font-semibold text-slate-800 mb-1">{item.title}</h3>
                  <p className="text-sm text-slate-500 leading-relaxed">{item.body}</p>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ── Feature highlights ─────────────────────────────── */}
      <section className="max-w-5xl mx-auto px-4 py-16 w-full">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider text-center mb-2">
          What's under the hood
        </p>
        <h2 className="text-2xl font-bold text-slate-900 text-center mb-10">
          Every tool you need to walk in confident
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {FEATURES.map((f) => (
            <Card key={f.title}>
              <div className="w-9 h-9 rounded-xl bg-violet-50 flex items-center justify-center mb-4">
                {f.icon}
              </div>
              <h3 className="font-semibold text-slate-800 mb-1">{f.title}</h3>
              <p className="text-sm text-slate-500 leading-relaxed">{f.body}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* ── Sample output preview ──────────────────────────── */}
      <section className="bg-white/40 backdrop-blur-sm border-y border-white/50">
        <div className="max-w-5xl mx-auto px-4 py-16">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider text-center mb-2">
            Sample Output
          </p>
          <h2 className="text-2xl font-bold text-slate-900 text-center mb-10">
            See what a mock interview feedback report looks like
          </h2>
          <div className="max-w-xl mx-auto">
            <Card className="space-y-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                    Overall Score
                  </p>
                  <div className="flex items-end gap-2">
                    <span className="text-5xl font-bold text-emerald-600">8.2</span>
                    <span className="text-xl text-slate-300 mb-1">/10</span>
                  </div>
                </div>
                <span className="bg-emerald-100 text-emerald-700 text-sm font-medium px-3 py-1.5 rounded-full">
                  Strong Performance
                </span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500 rounded-full" style={{ width: "82%" }} />
              </div>
              <div className="border-t border-slate-100 pt-4">
                <p className="text-xs text-slate-400 uppercase tracking-wider mb-2">
                  Feedback Summary
                </p>
                <p className="text-sm text-slate-600 leading-relaxed italic">
                  "Clear communication and relevant examples throughout. The biggest opportunity is
                  adding sharper metrics and more explicit business impact to your strongest
                  answers."
                </p>
              </div>
              <div className="grid grid-cols-3 gap-2 pt-1">
                {[
                  { label: "Relevance", score: 9 },
                  { label: "Clarity", score: 8 },
                  { label: "Industry Fit", score: 8 },
                ].map((s) => (
                  <div key={s.label} className="text-center bg-slate-50/80 rounded-xl p-3">
                    <p className="text-lg font-bold text-slate-800">{s.score}</p>
                    <p className="text-xs text-slate-400 mt-0.5">{s.label}</p>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* ── FAQ ────────────────────────────────────────────── */}
      <section className="max-w-3xl mx-auto px-4 py-16 w-full">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider text-center mb-2">
          FAQ
        </p>
        <h2 className="text-2xl font-bold text-slate-900 text-center mb-10">Common questions</h2>
        <div className="space-y-3">
          {FAQ.map((item) => (
            <details
              key={item.q}
              className="group bg-white/70 backdrop-blur-sm rounded-2xl border border-white/60 shadow-sm"
            >
              <summary className="flex items-center justify-between cursor-pointer list-none px-5 py-4">
                <span className="text-sm font-medium text-slate-800">{item.q}</span>
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
              <p className="px-5 pb-4 text-sm text-slate-500 leading-relaxed">{item.a}</p>
            </details>
          ))}
        </div>
      </section>

      {/* ── Footer CTA ─────────────────────────────────────── */}
      <section className="bg-white/40 backdrop-blur-sm border-t border-white/50">
        <div className="max-w-2xl mx-auto px-4 py-16 text-center">
          <h2 className="text-2xl font-bold text-slate-900 mb-3">
            Practice before your next interview.
          </h2>
          <p className="text-slate-500 text-sm mb-8">
            Rehearse your answers, handle follow-up questions, and review structured feedback — all
            before the real thing.
          </p>
          {isSignedIn ? (
            <Link href="/dashboard">
              <Button size="lg">Go to My Practice →</Button>
            </Link>
          ) : (
            <Button size="lg" onClick={() => signIn("google")}>
              Start with Google
            </Button>
          )}
        </div>
      </section>

      <Footer />
    </div>
  )
}
