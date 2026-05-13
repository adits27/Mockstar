import { type HTMLAttributes } from "react"
import { clsx } from "clsx"

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  padded?: boolean
}

export function Card({ className, padded = true, ...props }: CardProps) {
  return (
    <div
      className={clsx(
        "bg-white rounded-2xl border border-slate-100 shadow-sm",
        padded && "p-6",
        className,
      )}
      {...props}
    />
  )
}
