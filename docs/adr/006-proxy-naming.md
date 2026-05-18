# ADR 006 — Route Guard Named `proxy.ts` Instead of `middleware.ts`

**Status:** Accepted  
**Date:** 2026-05

---

## Context

Next.js route guards are conventionally placed in a file called `middleware.ts` at the project root. This file is picked up automatically by the Next.js runtime based on filename convention.

However, Next.js 16 introduced breaking changes to how `middleware.ts` interacts with NextAuth v5 beta — specifically around how auth state is read inside the middleware edge runtime. During development, the standard `middleware.ts` approach produced inconsistent auth state reads under the NextAuth v5 beta session model.

## Decision

The route guard is placed in **`frontend/src/proxy.ts`** instead of `middleware.ts`. Next.js still picks it up as middleware via the exported `matcher` config and the file path resolution — the naming is unconventional but fully functional.

This is documented explicitly in `CLAUDE.md` to prevent a future developer from assuming the guard is missing and recreating it as `middleware.ts`, which would cause a conflict.

## Consequences

**Benefits:**
- Avoids the NextAuth v5 + Next.js 16 middleware edge runtime compatibility issue
- Auth state is read reliably on every request to protected routes
- The guard logic itself is unchanged — it redirects unauthenticated users from `/dashboard`, `/interview`, `/sessions`, and `/onboarding` to `/`

**Trade-offs:**
- Non-standard naming is surprising to developers unfamiliar with the codebase — mitigated by the CLAUDE.md documentation
- If Next.js or NextAuth resolves the underlying compatibility issue in a future release, the file should be renamed to `middleware.ts` for clarity

**Source files:** `frontend/src/proxy.ts`, `frontend/src/auth.ts`
