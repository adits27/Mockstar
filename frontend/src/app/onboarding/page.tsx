"use client"

import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useState } from "react"
import Image from "next/image"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"
import { uploadResume } from "@/lib/api"

const EXPERIENCE_LEVELS = ["Student / Internship", "Junior (0–2 yrs)", "Mid-level (3–5 yrs)", "Senior (6+ yrs)"]
const CHALLENGES = [
  "Filler words",
  "Pacing",
  "Stutter / stammer",
  "Non-native English speaker",
  "Eye contact",
  "Structuring answers",
  "ADHD",
  "Anxiety",
  "Autistic",
  "Strabismus",
  "Nystagmus",
  "Tourette syndrome",
  "Aphasia",
  "Deaf / hard of hearing",
  "Cluttering",
]

export default function Onboarding() {
  const { data: session } = useSession()
  const router = useRouter()

  const [step, setStep] = useState<1 | 2>(1)
  const [experience, setExperience] = useState("")
  const [goals, setGoals] = useState("")
  const [selectedChallenges, setSelectedChallenges] = useState<string[]>([])
  const [file, setFile] = useState<File | null>(null)
  const [linkedin, setLinkedin] = useState("")
  const [github, setGithub] = useState("")
  const [portfolio, setPortfolio] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function toggleChallenge(c: string) {
    setSelectedChallenges((prev) =>
      prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c],
    )
  }

  async function handleFinish() {
    if (!session?.user.id) return
    if (!file) {
      setError("Please upload your resume to continue.")
      return
    }
    setLoading(true)
    setError(null)
    try {
      await uploadResume(session.user.id, file)
      router.replace("/dashboard")
    } catch {
      setError("Upload failed — please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-16">
      <div className="w-full max-w-lg">
        <div className="mb-8 flex flex-col items-center">
          <div className="w-[118px] h-[30px] relative overflow-hidden rounded-md mb-2">
            <Image
              src="/logos/mockstar_logo.png"
              alt="MockStar"
              fill
              style={{ objectFit: "cover", objectPosition: "center 50%" }}
              priority
            />
          </div>
          <p className="text-slate-400 text-sm mt-1">Step {step} of 2</p>
        </div>

        {step === 1 && (
          <Card>
            <h2 className="text-xl font-semibold mb-6">Tell us about yourself</h2>

            <label className="block mb-4">
              <span className="text-sm font-medium text-slate-700 mb-1.5 block">
                Experience level
              </span>
              <div className="grid grid-cols-2 gap-2">
                {EXPERIENCE_LEVELS.map((lvl) => (
                  <button
                    key={lvl}
                    type="button"
                    onClick={() => setExperience(lvl)}
                    className={`px-3 py-2 text-sm rounded-xl border transition-all ${
                      experience === lvl
                        ? "border-violet-600 bg-violet-600 text-white"
                        : "border-slate-200 text-slate-600 hover:border-slate-400"
                    }`}
                  >
                    {lvl}
                  </button>
                ))}
              </div>
            </label>

            <label className="block mb-4">
              <span className="text-sm font-medium text-slate-700 mb-1.5 block">
                Communication challenges{" "}
                <span className="text-slate-400 font-normal">(optional)</span>
              </span>
              <div className="flex flex-wrap gap-2">
                {CHALLENGES.map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => toggleChallenge(c)}
                    className={`px-3 py-1.5 text-sm rounded-full border transition-all ${
                      selectedChallenges.includes(c)
                        ? "border-violet-600 bg-violet-600 text-white"
                        : "border-slate-200 text-slate-600 hover:border-slate-400"
                    }`}
                  >
                    {c}
                  </button>
                ))}
              </div>
            </label>

            <label className="block mb-6">
              <span className="text-sm font-medium text-slate-700 mb-1.5 block">
                What do you want to improve?{" "}
                <span className="text-slate-400 font-normal">(optional)</span>
              </span>
              <textarea
                value={goals}
                onChange={(e) => setGoals(e.target.value)}
                rows={2}
                placeholder="e.g. answer more concisely, reduce filler words…"
                className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500 resize-none"
              />
            </label>

            <Button className="w-full" onClick={() => setStep(2)} disabled={!experience}>
              Continue
            </Button>
          </Card>
        )}

        {step === 2 && (
          <Card>
            <h2 className="text-xl font-semibold mb-2">Upload your resume</h2>
            <p className="text-sm text-slate-500 mb-6">
              Your resume is used to tailor questions and suggest stronger stories in feedback. PDF
              or DOCX, up to 10 MB.
            </p>

            <label className="block mb-6 cursor-pointer">
              <div
                className={`border-2 border-dashed rounded-2xl p-8 text-center transition-colors ${
                  file ? "border-violet-500 bg-violet-50" : "border-slate-200 hover:border-violet-400"
                }`}
              >
                <input
                  type="file"
                  accept=".pdf,.docx,.doc"
                  className="sr-only"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                />
                {file ? (
                  <p className="text-sm font-medium text-slate-800">✓ {file.name}</p>
                ) : (
                  <>
                    <p className="text-sm font-medium text-slate-700">
                      Click to choose a file
                    </p>
                    <p className="text-xs text-slate-400 mt-1">PDF or DOCX</p>
                  </>
                )}
              </div>
            </label>

            <div className="mb-6">
              <span className="text-sm font-medium text-slate-700 mb-3 block">
                Online profiles{" "}
                <span className="text-slate-400 font-normal">(optional)</span>
              </span>
              <div className="space-y-3">
                <input
                  type="url"
                  value={linkedin}
                  onChange={(e) => setLinkedin(e.target.value)}
                  placeholder="LinkedIn — https://linkedin.com/in/yourname"
                  className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
                <input
                  type="url"
                  value={github}
                  onChange={(e) => setGithub(e.target.value)}
                  placeholder="GitHub — https://github.com/yourname"
                  className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
                <input
                  type="url"
                  value={portfolio}
                  onChange={(e) => setPortfolio(e.target.value)}
                  placeholder="Portfolio / Blog — https://yoursite.com"
                  className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </div>
            </div>

            {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

            <div className="flex gap-3">
              <Button variant="secondary" onClick={() => setStep(1)}>
                Back
              </Button>
              <Button className="flex-1" onClick={handleFinish} loading={loading}>
                {loading ? "Uploading…" : "Finish setup"}
              </Button>
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}
