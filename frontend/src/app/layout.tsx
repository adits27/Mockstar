import type { Metadata } from "next"
import { Geist } from "next/font/google"
import { SessionProvider } from "next-auth/react"
import "./globals.css"

const geist = Geist({ subsets: ["latin"], variable: "--font-geist" })

export const metadata: Metadata = {
  title: "MockStar — AI Interview Practice",
  description: "Practise interviews with AI-powered audio and video feedback.",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geist.variable} h-full antialiased`}>
      <body className="min-h-full bg-slate-50 text-slate-900 font-sans">
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  )
}
