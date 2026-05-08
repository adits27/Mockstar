import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.whisper import transcribe


@pytest.fixture
def mock_whisper_response():
    word1 = MagicMock()
    word1.word = "hello"
    word1.start = 0.0
    word1.end = 0.4

    word2 = MagicMock()
    word2.word = "world"
    word2.start = 0.5
    word2.end = 0.9

    response = MagicMock()
    response.text = "hello world"
    response.words = [word1, word2]
    response.duration = 1.0
    return response


async def test_transcribe_returns_transcript_and_words(mock_whisper_response):
    mock_file = MagicMock()
    mock_file.filename = "audio.webm"
    mock_file.content_type = "audio/webm"
    mock_file.read = AsyncMock(return_value=b"fake-audio-bytes")

    with patch("app.services.whisper.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.audio.transcriptions.create = AsyncMock(return_value=mock_whisper_response)

        result = await transcribe(mock_file)

    assert result["text"] == "hello world"
    assert result["duration"] == 1.0
    assert result["words"] == [
        {"word": "hello", "start": 0.0, "end": 0.4},
        {"word": "world", "start": 0.5, "end": 0.9},
    ]


async def test_transcribe_calls_whisper_with_verbose_json(mock_whisper_response):
    mock_file = MagicMock()
    mock_file.filename = "audio.webm"
    mock_file.content_type = "audio/webm"
    mock_file.read = AsyncMock(return_value=b"bytes")

    with patch("app.services.whisper.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        create_mock = AsyncMock(return_value=mock_whisper_response)
        instance.audio.transcriptions.create = create_mock

        await transcribe(mock_file)

        call_kwargs = create_mock.call_args.kwargs
        assert call_kwargs["model"] == "whisper-1"
        assert call_kwargs["response_format"] == "verbose_json"
        assert "word" in call_kwargs["timestamp_granularities"]
