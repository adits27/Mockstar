"use client"

import Link from "next/link"
import Image from "next/image"
import { signOut, useSession } from "next-auth/react"
import { Button } from "@/components/ui/Button"

export function Navbar() {
  const { data: session } = useSession()

  return (
    <header className="sticky top-0 z-40 bg-gradient-to-r from-violet-50/95 via-white/90 to-purple-50/95 backdrop-blur-md shadow-sm border-b border-violet-100/60">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="shrink-0">
          <div className="w-[118px] h-[30px] relative overflow-hidden rounded-md">
            <Image
              src="/logos/mockstar_logo.png"
              alt="MockStar"
              fill
              style={{ objectFit: "cover", objectPosition: "center 50%" }}
              priority
            />
          </div>
        </Link>

        <nav className="flex items-center gap-0.5">
          <Link
            href="/dashboard"
            className="text-sm font-semibold text-slate-700 hover:text-violet-700 px-3.5 py-2 rounded-lg hover:bg-violet-50 transition-colors"
          >
            My Practice
          </Link>
          <Link
            href="/about"
            className="text-sm font-semibold text-slate-700 hover:text-violet-700 px-3.5 py-2 rounded-lg hover:bg-violet-50 transition-colors"
          >
            About
          </Link>
          <Link
            href="/pricing"
            className="flex items-center gap-1.5 text-sm font-semibold text-slate-700 hover:text-violet-700 px-3.5 py-2 rounded-lg hover:bg-violet-50 transition-colors"
          >
            Pricing
            <span className="text-[10px] font-semibold bg-violet-100 text-violet-600 rounded-full px-1.5 py-0.5 leading-none">
              Soon
            </span>
          </Link>
        </nav>

        {session?.user && (
          <div className="flex items-center gap-3">
            {session.user.image && (
              <Image
                src={session.user.image}
                alt={session.user.name ?? "User"}
                width={40}
                height={40}
                className="rounded-full ring-2 ring-violet-100"
              />
            )}
            <Button variant="ghost" size="sm" onClick={() => signOut({ callbackUrl: "/" })}>
              Sign out
            </Button>
          </div>
        )}
      </div>
    </header>
  )
}
