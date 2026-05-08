import re

FILLER_PATTERNS: list[tuple[str, str]] = [
    ("you know", r"\byou know\b"),
    ("kind of", r"\bkind of\b"),
    ("sort of", r"\bsort of\b"),
    ("um", r"\bum\b"),
    ("uh", r"\buh\b"),
    ("like", r"\blike\b"),
    ("so", r"\bso\b"),
    ("basically", r"\bbasically\b"),
    ("literally", r"\bliterally\b"),
    ("actually", r"\bactually\b"),
    ("right", r"\bright\b"),
]


def detect_fillers(transcript: str) -> dict[str, int]:
    text = transcript.lower()
    counts: dict[str, int] = {}
    for label, pattern in FILLER_PATTERNS:
        matches = len(re.findall(pattern, text))
        if matches:
            counts[label] = matches
    return counts


def detect_pauses(words: list[dict], threshold: float = 1.5) -> int:
    if len(words) < 2:
        return 0
    return sum(
        1
        for i in range(1, len(words))
        if words[i]["start"] - words[i - 1]["end"] > threshold
    )


def calculate_wpm(word_count: int, duration_seconds: float) -> float:
    if duration_seconds == 0:
        return 0.0
    return round(word_count / duration_seconds * 60, 1)
