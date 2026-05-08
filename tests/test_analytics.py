from app.services.analytics import detect_fillers, detect_pauses, calculate_wpm


def test_detect_fillers_counts_single_word_fillers():
    transcript = "I um worked at like Google and um left"
    result = detect_fillers(transcript)
    assert result["um"] == 2
    assert result["like"] == 1


def test_detect_fillers_counts_phrase_fillers():
    transcript = "It was you know kind of a big deal"
    result = detect_fillers(transcript)
    assert result["you know"] == 1
    assert result["kind of"] == 1


def test_detect_fillers_returns_empty_for_clean_speech():
    transcript = "My experience includes three years of backend development."
    result = detect_fillers(transcript)
    assert result == {}


def test_detect_fillers_is_case_insensitive():
    transcript = "Um that was Like a big deal"
    result = detect_fillers(transcript)
    assert result["um"] == 1
    assert result["like"] == 1


def test_detect_pauses_counts_gaps_above_threshold():
    words = [
        {"word": "hello", "start": 0.0, "end": 0.4},
        {"word": "world", "start": 2.0, "end": 2.4},   # 1.6s gap → pause
        {"word": "bye", "start": 2.5, "end": 2.8},     # 0.1s gap → no pause
    ]
    assert detect_pauses(words, threshold=1.5) == 1


def test_detect_pauses_returns_zero_for_fluent_speech():
    words = [
        {"word": "I", "start": 0.0, "end": 0.1},
        {"word": "speak", "start": 0.15, "end": 0.5},
        {"word": "fast", "start": 0.55, "end": 0.9},
    ]
    assert detect_pauses(words) == 0


def test_detect_pauses_returns_zero_for_empty_words():
    assert detect_pauses([]) == 0


def test_calculate_wpm_basic():
    assert calculate_wpm(word_count=150, duration_seconds=60.0) == 150.0


def test_calculate_wpm_rounds_to_one_decimal():
    assert calculate_wpm(word_count=100, duration_seconds=45.0) == 133.3


def test_calculate_wpm_returns_zero_for_zero_duration():
    assert calculate_wpm(word_count=10, duration_seconds=0.0) == 0.0
