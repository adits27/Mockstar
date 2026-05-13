import google.generativeai as genai

from app.config import settings


def build_next_question_prompt(session_data: dict) -> str:
    metadata = session_data["metadata"]
    turns = session_data["turns"]
    job_role = metadata.get("job_role", "not specified")
    interview_type = metadata.get("interview_type", "general")
    company_name = metadata.get("company_name") or ""
    job_description = metadata.get("job_description") or ""
    resume_text = metadata.get("resume_text") or ""

    company_line = f" at {company_name}" if company_name else ""
    jd_section = f"\nJob description:\n{job_description[:3000]}\n" if job_description else ""
    resume_section = f"\nCandidate resume:\n{resume_text[:2000]}\n" if resume_text else ""

    if not turns:
        return f"""You are conducting a {interview_type} interview for a {job_role} position{company_line}.
{jd_section}{resume_section}
Generate a single opening interview question tailored to this candidate and role. Return only the question text, no preamble."""

    history = "\n\n".join(
        f"Q: {t['question_text']}\nA: {t['transcript']}"
        for t in turns
    )

    return f"""You are conducting a {interview_type} interview for a {job_role} position{company_line}.
{jd_section}{resume_section}
Interview so far:
{history}

Based on the candidate's last answer, generate one focused follow-up question that probes deeper or explores a relevant new area. Return only the question text, no preamble."""


async def generate_next_question(session_data: dict) -> str:
    genai.configure(api_key=settings.google_api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = build_next_question_prompt(session_data)
    response = await model.generate_content_async(prompt)
    return response.text.strip()
