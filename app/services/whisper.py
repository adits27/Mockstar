from openai import AsyncOpenAI
from fastapi import UploadFile

from app.config import settings


async def transcribe(audio_file: UploadFile) -> dict:
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    audio_bytes = await audio_file.read()

    response = await client.audio.transcriptions.create(
        model="whisper-1",
        file=(audio_file.filename, audio_bytes, audio_file.content_type),
        response_format="verbose_json",
        timestamp_granularities=["word"],
    )

    return {
        "text": response.text,
        "words": [{"word": w.word, "start": w.start, "end": w.end} for w in response.words],
        "duration": response.duration,
    }
