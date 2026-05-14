"use client"

import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"
import { PageShell } from "@/components/layout/PageShell"
import { createSession, extractDocumentText, getResume } from "@/lib/api"

const INTERVIEW_TYPES = ["Behavioral", "Technical", "Case study", "General"]
const QUESTION_COUNTS = [3, 5, 7]

export default function NewInterview() {
  const { data: session } = useSession()
  const router = useRouter()

  const [companyName, setCompanyName] = useState("")
  const [jobRole, setJobRole] = useState("")
  const [interviewType, setInterviewType] = useState("Behavioral")
  const [numQuestions, setNumQuestions] = useState(5)
  const [jdMode, setJdMode] = useState<"paste" | "upload" | "url">("paste")
  const [showUrlModal, setShowUrlModal] = useState(false)
  const [jdText, setJdText] = useState("")
  const [jdFile, setJdFile] = useState<File | null>(null)
  const [extracting, setExtracting] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleJdFileChange(file: File) {
    setJdFile(file)
    if (!session?.user.id) return
    setExtracting(true)
    try {
      const { text } = await extractDocumentText(session.user.id, file)
      setJdText(text)
    } catch {
      setError("Could not extract text from that file. Please paste the job description instead.")
      setJdMode("paste")
    } finally {
      setExtracting(false)
    }
  }

  async function handleStart() {
    if (!session?.user.id) return
    if (!jobRole.trim()) {
      setError("Please enter the job role.")
      return
    }
    setLoading(true)
    setError(null)
    try {
      let resumeText: string | undefined
      try {
        const resume = await getResume(session.user.id)
        resumeText = resume.resume_text
      } catch {
        // Resume not found — interview continues without it
      }

      const { session_id } = await createSession({
        user_id: session.user.id,
        job_role: jobRole,
        company_name: companyName,
        interview_type: interviewType.toLowerCase(),
        job_description: jdText || null,
        resume_text: resumeText ?? null,
        num_questions: numQuestions,
        user_profile: {},
      })
      router.push(`/interview/${session_id}?n=${numQuestions}`)
    } catch {
      setError("Failed to start session — is the backend running?")
    } finally {
      setLoading(false)
    }
  }

  return (
    <PageShell>
      <div className="max-w-xl mx-auto">
        <h1 className="text-2xl font-bold text-slate-900 mb-8">Set up your interview</h1>

        <div className="space-y-6">
          <Card>
            <h2 className="font-semibold text-slate-800 mb-4">Role details</h2>
            <div className="space-y-4">
              <label className="block">
                <span className="text-sm font-medium text-slate-700 mb-1.5 block">Job role *</span>
                <input
                  value={jobRole}
                  onChange={(e) => setJobRole(e.target.value)}
                  placeholder="e.g. Senior Software Engineer"
                  className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </label>
              <label className="block">
                <span className="text-sm font-medium text-slate-700 mb-1.5 block">
                  Company name <span className="text-slate-400 font-normal">(optional)</span>
                </span>
                <input
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="e.g. Acme Corp"
                  className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </label>
            </div>
          </Card>

          <Card>
            <h2 className="font-semibold text-slate-800 mb-4">Interview format</h2>
            <div className="space-y-4">
              <div>
                <span className="text-sm font-medium text-slate-700 mb-2 block">Type</span>
                <div className="grid grid-cols-2 gap-2">
                  {INTERVIEW_TYPES.map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setInterviewType(t)}
                      className={`px-3 py-2 text-sm rounded-xl border transition-all ${
                        interviewType === t
                          ? "border-violet-600 bg-violet-600 text-white"
                          : "border-slate-200 text-slate-600 hover:border-slate-400"
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <span className="text-sm font-medium text-slate-700 mb-2 block">
                  Number of questions
                </span>
                <div className="flex gap-2">
                  {QUESTION_COUNTS.map((n) => (
                    <button
                      key={n}
                      type="button"
                      onClick={() => setNumQuestions(n)}
                      className={`flex-1 py-2 text-sm rounded-xl border transition-all ${
                        numQuestions === n
                          ? "border-violet-600 bg-violet-600 text-white"
                          : "border-slate-200 text-slate-600 hover:border-slate-400"
                      }`}
                    >
                      {n}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <h2 className="font-semibold text-slate-800 mb-1">Job description</h2>
            <p className="text-xs text-slate-400 mb-4">
              Optional but recommended — helps tailor questions to the role.
            </p>
            <div className="flex gap-2 mb-4">
              {(["paste", "upload", "url"] as const).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => {
                    if (m === "url") { setShowUrlModal(true) }
                    setJdMode(m)
                  }}
                  className={`flex-1 py-2 text-sm rounded-xl border transition-all ${
                    jdMode === m
                      ? "border-violet-600 bg-violet-600 text-white"
                      : "border-slate-200 text-slate-600 hover:border-slate-400"
                  }`}
                >
                  {m === "paste" ? "Paste text" : m === "upload" ? "Upload file" : "URL"}
                </button>
              ))}
            </div>
            {jdMode === "paste" && (
              <textarea
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                rows={6}
                placeholder="Paste the job description here…"
                className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500 resize-none"
              />
            )}
            {jdMode === "upload" && (
              <label className="block cursor-pointer">
                <div
                  className={`border-2 border-dashed rounded-2xl p-6 text-center transition-colors ${
                    jdFile ? "border-violet-500 bg-violet-50" : "border-slate-200 hover:border-violet-400"
                  }`}
                >
                  <input
                    type="file"
                    accept=".pdf,.docx,.doc"
                    className="sr-only"
                    onChange={(e) => {
                      const f = e.target.files?.[0]
                      if (f) handleJdFileChange(f)
                    }}
                  />
                  {extracting ? (
                    <p className="text-sm text-slate-500">Extracting text…</p>
                  ) : jdFile ? (
                    <p className="text-sm font-medium text-slate-800">✓ {jdFile.name}</p>
                  ) : (
                    <p className="text-sm text-slate-500">Click to upload PDF or DOCX</p>
                  )}
                </div>
              </label>
            )}
            {jdMode === "url" && (
              <input
                type="url"
                placeholder="https://example.com/job-posting"
                className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500"
                readOnly
              />
            )}

            {/* URL modal */}
            {showUrlModal && (
              <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 px-4">
                <Card className="max-w-sm w-full">
                  <h3 className="font-semibold text-slate-800 mb-2">Heads up</h3>
                  <p className="text-sm text-slate-600 mb-5">
                    Please paste the JD text or save as PDF and upload, because some websites block scraping.
                  </p>
                  <Button
                    className="w-full"
                    onClick={() => { setShowUrlModal(false); setJdMode("paste") }}
                  >
                    Got it
                  </Button>
                </Card>
              </div>
            )}
          </Card>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <Button className="w-full" size="lg" onClick={handleStart} loading={loading}>
            Begin interview
          </Button>
        </div>
      </div>
    </PageShell>
  )
}
