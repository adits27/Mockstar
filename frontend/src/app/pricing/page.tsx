import Link from "next/link"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"
import { PageShell } from "@/components/layout/PageShell"

const PLANNED_TIERS = [
  {
    name: "Free",
    description: "Perfect for getting started with AI interview practice.",
    highlights: ["5 mock interviews per month", "Speech analytics & transcription", "Structured feedback report"],
    color: "border-slate-200",
    badge: null,
  },
  {
    name: "Pro",
    description: "For candidates actively preparing for roles.",
    highlights: [
      "Unlimited mock interviews",
      "Full speech + gaze analysis",
      "Question-by-question breakdown",
      "Resume upload & tailored questions",
      "Progress tracking over time",
    ],
    color: "border-violet-400",
    badge: "Most Popular",
  },
  {
    name: "Teams",
    description: "For career centers, universities, and employer training programs.",
    highlights: [
      "Everything in Pro",
      "Cohort management dashboard",
      "Aggregate analytics & reporting",
      "Custom interview templates",
      "Dedicated support",
    ],
    color: "border-teal-400",
    badge: null,
  },
]

export default function PricingPage() {
  return (
    <PageShell>
      <div className="max-w-4xl mx-auto space-y-12">
        {/* Header */}
        <div className="text-center pt-4">
          <span className="inline-block px-3 py-1 text-xs font-medium bg-amber-100 text-amber-700 rounded-full mb-4">
            Coming Soon
          </span>
          <h1 className="text-4xl font-bold text-slate-900 mb-4">Simple, transparent pricing</h1>
          <p className="text-slate-500 leading-relaxed max-w-xl mx-auto">
            MockStar is currently free to use while we&apos;re in beta. Paid plans are on the
            roadmap — sign up to be notified when they launch.
          </p>
        </div>

        {/* Tier cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 opacity-70 pointer-events-none select-none">
          {PLANNED_TIERS.map((tier) => (
            <Card
              key={tier.name}
              className={`relative border-2 ${tier.color} flex flex-col`}
            >
              {tier.badge && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 text-xs font-semibold bg-violet-600 text-white rounded-full px-3 py-1">
                  {tier.badge}
                </span>
              )}
              <p className="text-lg font-bold text-slate-800 mb-1">{tier.name}</p>
              <p className="text-sm text-slate-500 mb-5 leading-relaxed">{tier.description}</p>
              <ul className="space-y-2 flex-1">
                {tier.highlights.map((h) => (
                  <li key={h} className="flex items-start gap-2 text-sm text-slate-600">
                    <span className="text-emerald-500 mt-0.5 shrink-0">✓</span>
                    {h}
                  </li>
                ))}
              </ul>
              <div className="mt-6 h-9 bg-slate-100 rounded-xl" />
            </Card>
          ))}
        </div>

        <p className="text-center text-xs text-slate-400">
          Pricing and features are illustrative and subject to change.
        </p>

        {/* CTA */}
        <div className="text-center pb-4">
          <p className="text-slate-500 text-sm mb-5">
            In the meantime, MockStar is completely free — no account limits.
          </p>
          <Link href="/interview/new">
            <Button size="lg">Start practicing for free</Button>
          </Link>
        </div>
      </div>
    </PageShell>
  )
}
