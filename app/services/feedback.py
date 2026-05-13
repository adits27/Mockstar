import json

import google.generativeai as genai
from google.generativeai import GenerationConfig

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

    return f"""You are an expert, inclusive interview coach evaluating a mock interview.

User profile:
- Communication challenges: {challenges}
- Experience level: {experience}
- Goals: {goals}

Do not penalize the user for documented communication differences listed above.
Do not factor speaking pace or speed into any score or feedback.

Interview context:
- Job role: {metadata.get("job_role", "not specified")}
- Interview type: {metadata.get("interview_type", "general")}

Interview turns:
{turns_text}

Score the candidate on each dimension using this anchored scale:
- 1-4: Below expectations (significant gaps, vague or off-topic)
- 5-6: Meets basic expectations (adequate but room for improvement)
- 7-8: Strong performance (clear, specific, relevant — minor refinements needed)
- 9-10: Exceptional (rare; outstanding depth, precision, and relevance)

Dimensions to score (integers 1-10):
- answer_relevance: Did the answer directly address what was asked?
- experience_articulation: Were examples specific, credible, and well-described?
- industry_fit: Did the candidate use appropriate terminology and demonstrate domain awareness?
- clarity_and_structure: Was the answer well-organized and easy to follow?
- filler_word_usage: How polished was delivery? (10 = no fillers, lower scores only for heavy, disruptive usage)

Return a JSON object with exactly this structure:
{{
  "scores": {{
    "answer_relevance": <int>,
    "experience_articulation": <int>,
    "industry_fit": <int>,
    "clarity_and_structure": <int>,
    "filler_word_usage": <int>,
    "overall": <float, weighted average>
  }},
  "feedback": "<markdown feedback report covering: content quality and relevance, communication clarity, filler word patterns (framed constructively), strengths observed, specific areas for improvement with actionable suggestions>"
}}"""


async def generate_feedback(session_data: dict) -> dict:
    genai.configure(api_key=settings.google_api_key)
    model = genai.GenerativeModel(
        "gemini-2.5-flash",
        generation_config=GenerationConfig(response_mime_type="application/json"),
    )
    prompt = build_feedback_prompt(session_data)
    response = await model.generate_content_async(prompt)
    return json.loads(response.text)
