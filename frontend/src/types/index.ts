// NextAuth augmentations
declare module "next-auth" {
  interface Session {
    user: {
      id: string
      name?: string | null
      email?: string | null
      image?: string | null
    }
  }
}


// Backend API types

export interface CreateSessionRequest {
  user_id: string
  job_role?: string
  interview_type?: string
  company_name?: string
  job_description?: string | null
  resume_text?: string | null
  num_questions?: number
  user_profile?: {
    communication_challenges?: string[]
    experience_level?: string
    goals?: string
  }
}

export interface SessionSummary {
  session_id: string
  job_role: string
  interview_type: string
  created_at: string
  completed_at: string | null
  overall_score: number | null
}

export interface TurnResponse {
  turn_id: string
  transcript: string
}

export interface NextQuestionResponse {
  question: string
}

export interface ScoreBreakdown {
  answer_relevance: number
  experience_articulation: number
  industry_fit: number
  clarity_and_structure: number
  filler_word_usage: number
  eye_contact_and_presence?: number
  overall: number
}

export interface FeedbackResponse {
  feedback: string
  scores: ScoreBreakdown
  confidence_score?: number
  confidence_label?: string
  observations?: string[]
}

export interface SessionDetail {
  session_id: string
  job_role: string
  interview_type: string
  user_profile: Record<string, unknown>
  turns: TurnSummary[]
  feedback: string | null
  scores?: ScoreBreakdown
  confidence_score?: number
  confidence_label?: string
  observations?: string[]
}

export interface TurnSummary {
  turn_index: number
  question_text: string
  transcript: string
  filler_words: Record<string, number>
  pause_count: number
  wpm: number | null
}

export interface ResumeResponse {
  resume_text: string
  filename: string | null
  uploaded_at: string
}
