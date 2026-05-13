"use client"

import Link from "next/link"
import Image from "next/image"
import { signOut, useSession } from "next-auth/react"
import { Button } from "@/components/ui/Button"

export function Navbar() {
  const { data: session } = useSession()

  return (
    <header className="sticky top-0 z-40 bg-white/80 backdrop-blur border-b border-white/50">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/" className="shrink-0">
          <div className="w-[118px] h-[30px] relative overflow-hidden rounded-md">
            <Image
              src="/mockstar_logo.png"
              alt="MockStar"
              fill
              style={{ objectFit: "cover", objectPosition: "center 50%" }}
              priority
            />
          </div>
        </Link>

        <nav className="flex items-center gap-1">
          <Link
            href="/dashboard"
            className="text-sm text-slate-500 hover:text-slate-900 px-3 py-1.5 rounded-lg hover:bg-white/60 transition-colors"
          >
            My Practice
          </Link>
          <Link
            href="/about"
            className="text-sm text-slate-500 hover:text-slate-900 px-3 py-1.5 rounded-lg hover:bg-white/60 transition-colors"
          >
            About
          </Link>
          <Link
            href="/pricing"
            className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 px-3 py-1.5 rounded-lg hover:bg-white/60 transition-colors"
          >
            Pricing
            <span className="text-[10px] font-medium bg-violet-100 text-violet-500 rounded-full px-1.5 py-0.5 leading-none">
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
                width={32}
                height={32}
                className="rounded-full"
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
