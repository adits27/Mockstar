import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.feedback import build_feedback_prompt, generate_feedback


def test_build_feedback_prompt_includes_user_profile():
    session_data = {
        "user_profile": {
            "communication_challenges": ["stammer"],
            "experience_level": "junior",
            "goals": "land first SWE job",
        },
        "metadata": {"job_role": "Software Engineer", "interview_type": "technical"},
        "turns": [
            {
                "turn_index": 0,
                "question_text": "Tell me about yourself.",
                "transcript": "Um I worked at Google.",
                "filler_words": {"um": 1},
                "pause_count": 2,
            }
        ],
    }
    prompt = build_feedback_prompt(session_data)
    assert "stammer" in prompt
    assert "junior" in prompt
    assert "Software Engineer" in prompt
    assert "Tell me about yourself" in prompt
    assert "Um I worked at Google" in prompt
    assert "um" in prompt


def test_build_feedback_prompt_excludes_wpm():
    session_data = {
        "user_profile": {"communication_challenges": [], "experience_level": "senior", "goals": ""},
        "metadata": {"job_role": "PM", "interview_type": "behavioral"},
        "turns": [
            {
                "turn_index": 0,
                "question_text": "Describe a challenge.",
                "transcript": "I led a team.",
                "filler_words": {},
                "pause_count": 0,
                "wpm": 145.0,
            }
        ],
    }
    prompt = build_feedback_prompt(session_data)
    assert "145" not in prompt
    assert "wpm" not in prompt.lower()


async def test_generate_feedback_returns_model_text():
    session_data = {
        "user_profile": {"communication_challenges": [], "experience_level": "mid", "goals": ""},
        "metadata": {"job_role": "SWE", "interview_type": "technical"},
        "turns": [{"turn_index": 0, "question_text": "Q?", "transcript": "A.", "filler_words": {}, "pause_count": 0}],
    }

    mock_response = MagicMock()
    mock_response.text = '{"scores": {"answer_relevance": 8, "experience_articulation": 7, "industry_fit": 7, "clarity_and_structure": 8, "filler_word_usage": 9, "overall": 7.8}, "feedback": "Great job on clarity."}'

    with patch("app.services.feedback.genai") as mock_genai:
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        result = await generate_feedback(session_data)

    assert result["feedback"] == "Great job on clarity."
    assert result["scores"]["answer_relevance"] == 8
    assert result["scores"]["overall"] == 7.8
