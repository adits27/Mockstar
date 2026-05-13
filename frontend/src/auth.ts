import NextAuth from "next-auth"
import Google from "next-auth/providers/google"

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    jwt({ token, profile }) {
      // profile is only present on first sign-in
      if (profile?.sub) (token as Record<string, unknown>).userId = profile.sub
      return token
    },
    session({ session, token }) {
      session.user.id = (token as Record<string, unknown>).userId as string
      return session
    },
  },
})
