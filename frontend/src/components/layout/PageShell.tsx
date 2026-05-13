import { type ReactNode } from "react"
import { Navbar } from "./Navbar"
import { Footer } from "./Footer"

export function PageShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-10">{children}</main>
      <Footer />
    </div>
  )
}
