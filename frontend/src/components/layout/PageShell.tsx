import { type ReactNode } from "react"
import { Navbar } from "./Navbar"

export function PageShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="max-w-6xl mx-auto px-4 py-10">{children}</main>
    </div>
  )
}
