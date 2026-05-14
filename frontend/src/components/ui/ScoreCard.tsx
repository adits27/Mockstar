import { clsx } from "clsx"

interface ScoreCardProps {
  label: string
  score: number
  maxScore?: number
  description?: string
}

export function ScoreCard({ label, score, maxScore = 10, description }: ScoreCardProps) {
  const pct = score / maxScore

  const color =
    pct >= 0.8
      ? { ring: "stroke-emerald-500", text: "text-emerald-600", bg: "bg-emerald-50" }
      : pct >= 0.6
        ? { ring: "stroke-amber-400", text: "text-amber-600", bg: "bg-amber-50" }
        : { ring: "stroke-red-400", text: "text-red-600", bg: "bg-red-50" }

  const circumference = 2 * Math.PI * 28
  const dashOffset = circumference * (1 - pct)

  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 flex flex-col items-center gap-3">
      <div className="relative w-20 h-20">
        <svg className="w-20 h-20 -rotate-90" viewBox="0 0 64 64">
          <circle cx="32" cy="32" r="28" fill="none" stroke="#f1f5f9" strokeWidth="5" />
          <circle
            cx="32"
            cy="32"
            r="28"
            fill="none"
            strokeWidth="5"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            className={clsx("transition-all duration-700", color.ring)}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={clsx("text-xl font-bold", color.text)}>{score}</span>
        </div>
      </div>
      <div className="text-center">
        <p className="text-sm font-medium text-slate-700 leading-tight">{label}</p>
        {description && <p className="text-xs text-slate-400 mt-0.5">{description}</p>}
      </div>
    </div>
  )
}
