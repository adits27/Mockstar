import google.generativeai as genai

from app.config import settings


def build_feedback_prompt(session_data: dict) -> str:
    profile = session_data["user_profile"]
    metadata = session_data["metadata"]
    turns = session_data["turns"]

    challenges = ", ".join(profile.get("communication_challenges", [])) or "none reported"
    experience = profile.get("experience_level", "not specified")
    goals = profile.get("goals", "general improvement")

    turns_text = "\n\n".join(
        f"Q{t['turn_index'] + 1}: {t['question_text']}\n"
        f"Answer: {t['transcript']}\n"
        f"Filler words: {t['filler_words'] or 'none detected'}\n"
        f"Significant pauses: {t['pause_count']}"
        for t in turns
    )

    return f"""You are an expert, inclusive interview coach.

User profile:
- Communication challenges: {challenges}
- Experience level: {experience}
- Goals: {goals}

Do not penalize the user for documented communication differences listed above.
Provide constructive, specific, and actionable feedback.

Interview context:
- Job role: {metadata.get("job_role", "not specified")}
- Interview type: {metadata.get("interview_type", "general")}

Interview turns:
{turns_text}

Generate a structured feedback report in markdown covering:
1. Content quality and relevance of answers
2. Communication clarity
3. Filler word patterns (frame constructively, not punitively)
4. Strengths observed
5. Specific areas for improvement with actionable suggestions
"""


async def generate_feedback(session_data: dict) -> str:
    genai.configure(api_key=settings.google_api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = build_feedback_prompt(session_data)
    response = await model.generate_content_async(prompt)
    return response.text
