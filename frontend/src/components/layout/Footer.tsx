import Image from "next/image"
import Link from "next/link"

export function Footer() {
  return (
    <footer className="mt-auto">
      {/* Upper footer — links + Berkeley logo */}
      <div className="bg-white/60 backdrop-blur-sm border-t border-slate-200/60">
        <div className="max-w-6xl mx-auto px-4 py-8 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-6 text-sm text-slate-500">
            <Link href="/" className="hover:text-violet-700 transition-colors">Home</Link>
            <Link href="/dashboard" className="hover:text-violet-700 transition-colors">My Practice</Link>
            <Link href="/about" className="hover:text-violet-700 transition-colors">About</Link>
            <Link href="/pricing" className="hover:text-violet-700 transition-colors">Pricing</Link>
          </div>
          <div className="w-[320px] h-[28px] relative">
            <Image
              src="/logos/berkeley_ischool_colored.svg"
              alt="UC Berkeley School of Information"
              fill
              style={{ objectFit: "contain", objectPosition: "right center" }}
            />
          </div>
        </div>
      </div>

      {/* Lower footer — dark gradient "Made with ❤️" strip */}
      <div className="bg-gradient-to-r from-slate-900 via-violet-950 to-purple-900">
        <div className="max-w-6xl mx-auto px-4 py-5 flex items-center justify-center gap-2.5">
          <span className="text-white/80 text-sm">Made with</span>
          <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-rose-500 shadow-sm text-white text-xs leading-none">
            ♥
          </span>
          <span className="text-white/80 text-sm">
            by{" "}
            <a
              href="https://www.linkedin.com/in/harshit-kaushik/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-white hover:text-violet-300 transition-colors"
            >
              Harshit Kaushik
            </a>
            ,{" "}
            <a
              href="https://www.linkedin.com/in/adithya27/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-white hover:text-violet-300 transition-colors"
            >
              Adithya Subramaniam
            </a>
            , and{" "}
            <a
              href="https://www.linkedin.com/in/vijay-kumar-prakash/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-white hover:text-violet-300 transition-colors"
            >
              VKP
            </a>
          </span>
        </div>
      </div>
    </footer>
  )
}
