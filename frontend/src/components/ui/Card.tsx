import { type HTMLAttributes } from "react"
import { clsx } from "clsx"

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  padded?: boolean
}

export function Card({ className, padded = true, ...props }: CardProps) {
  return (
    <div
      className={clsx(
        "bg-white/80 backdrop-blur-sm rounded-2xl border border-white/60 shadow-sm",
        padded && "p-6",
        className,
      )}
      {...props}
    />
  )
}
