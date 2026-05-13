import Link from "next/link"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"
import { PageShell } from "@/components/layout/PageShell"

const TEAM = [
  {
    name: "Harshit Kaushik",
    role: "Computer Vision",
    initials: "HK",
    colour: "bg-violet-100 text-violet-700",
    linkedin: "https://www.linkedin.com/in/harshit-kaushik/",
    github: "https://github.com/Pingo9o11",
  },
  {
    name: "Adithya Subramaniam",
    role: "Speech Processing",
    initials: "AS",
    colour: "bg-teal-100 text-teal-700",
    linkedin: "https://www.linkedin.com/in/adithya27/",
    github: "https://github.com/adits27",
  },
  {
    name: "Vijay Kumar Prakash",
    role: "Integrations, System Design & Product",
    initials: "VK",
    colour: "bg-pink-100 text-pink-700",
    linkedin: "https://www.linkedin.com/in/vijay-kumar-prakash/",
    github: "https://github.com/VijayKumarPrakash",
  },
]

const TECH = [
  "FastAPI",
  "Next.js 16",
  "PostgreSQL",
  "OpenAI Whisper",
  "Gemini 2.5 Flash",
  "OpenCV",
  "Tailwind CSS",
  "NextAuth.js",
]

export default function AboutPage() {
  return (
    <PageShell>
      <div className="max-w-2xl mx-auto space-y-12">
        {/* Header */}
        <div className="text-center pt-4">
          <span className="inline-block px-3 py-1 text-xs font-medium bg-violet-100 text-violet-700 rounded-full mb-4">
            Capstone project · 2026
          </span>
          <h1 className="text-3xl font-bold text-slate-900 mb-4">Meet the Team</h1>
          <p className="text-slate-500 leading-relaxed">
            MockStar was built as a capstone project in 2026 by a small team passionate about making
            interview preparation more intelligent and accessible.
          </p>
        </div>

        {/* Team cards */}
        <section>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {TEAM.map((member) => (
              <Card key={member.name} className="text-center">
                <div
                  className={`w-14 h-14 rounded-full ${member.colour} flex items-center justify-center text-lg font-bold mx-auto mb-3`}
                >
                  {member.initials}
                </div>
                <p className="font-semibold text-slate-800">{member.name}</p>
                <p className="text-xs text-slate-400 mt-1 mb-4">{member.role}</p>
                <div className="flex items-center justify-center gap-3">
                  <a
                    href={member.linkedin}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-slate-400 hover:text-violet-600 transition-colors"
                    aria-label={`${member.name} LinkedIn`}
                  >
                    {/* LinkedIn icon */}
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
                    </svg>
                  </a>
                  <a
                    href={member.github}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-slate-400 hover:text-slate-800 transition-colors"
                    aria-label={`${member.name} GitHub`}
                  >
                    {/* GitHub icon */}
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                    </svg>
                  </a>
                </div>
              </Card>
            ))}
          </div>
        </section>

        {/* Tech stack */}
        <section>
          <Card>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
              Built with
            </p>
            <div className="flex flex-wrap gap-2">
              {TECH.map((t) => (
                <span
                  key={t}
                  className="text-sm bg-slate-50 text-slate-600 border border-slate-100 rounded-full px-3 py-1"
                >
                  {t}
                </span>
              ))}
            </div>
          </Card>
        </section>

        {/* CTA */}
        <div className="text-center pb-4">
          <Link href="/">
            <Button size="lg">Try MockStar</Button>
          </Link>
        </div>
      </div>
    </PageShell>
  )
}
