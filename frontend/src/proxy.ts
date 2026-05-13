import { auth } from "@/auth"
import { NextResponse } from "next/server"

const PROTECTED = ["/dashboard", "/interview", "/sessions", "/onboarding"]

export const proxy = auth((req) => {
  const { pathname } = req.nextUrl
  const isProtected = PROTECTED.some((p) => pathname.startsWith(p))

  if (isProtected && !req.auth) {
    return NextResponse.redirect(new URL("/", req.url))
  }
})

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
}
