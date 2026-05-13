import google.generativeai as genai

from app.config import settings


def build_next_question_prompt(session_data: dict) -> str:
    metadata = session_data["metadata"]
    turns = session_data["turns"]
    job_role = metadata.get("job_role", "not specified")
    interview_type = metadata.get("interview_type", "general")

    if not turns:
        return f"""You are conducting a {interview_type} interview for a {job_role} position.

Generate a single opening interview question. Return only the question text, no preamble."""

    history = "\n\n".join(
        f"Q: {t['question_text']}\nA: {t['transcript']}"
        for t in turns
    )

    return f"""You are conducting a {interview_type} interview for a {job_role} position.

Interview so far:
{history}

Based on the candidate's last answer, generate one focused follow-up question that probes deeper or explores a relevant new area. Return only the question text, no preamble."""


async def generate_next_question(session_data: dict) -> str:
    genai.configure(api_key=settings.google_api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = build_next_question_prompt(session_data)
    response = await model.generate_content_async(prompt)
    return response.text.strip()
