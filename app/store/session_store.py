from datetime import datetime, timezone
from typing import Any, Optional

_store: dict[str, dict] = {}


def clear() -> None:
    _store.clear()


def create(session_id: str, user_profile: dict, metadata: dict) -> None:
    _store[session_id] = {
        "user_profile": user_profile,
        "metadata": metadata,
        "turns": [],
        "last_activity": datetime.now(timezone.utc),
    }


def get(session_id: str) -> Optional[dict]:
    return _store.get(session_id)


def add_turn(session_id: str, turn: dict[str, Any]) -> None:
    _store[session_id]["turns"].append(turn)
    _store[session_id]["last_activity"] = datetime.now(timezone.utc)


def update_turn_metrics(
    session_id: str,
    turn_index: int,
    filler_words: dict[str, int],
    pause_count: int,
    wpm: float,
) -> None:
    for turn in _store[session_id]["turns"]:
        if turn["turn_index"] == turn_index:
            turn["filler_words"] = filler_words
            turn["pause_count"] = pause_count
            turn["wpm"] = wpm
            return


def set_cv_result(session_id: str, result: dict) -> None:
    if session_id in _store:
        _store[session_id]["cv_result"] = result


def delete(session_id: str) -> None:
    _store.pop(session_id, None)


def purge_expired(max_idle_seconds: int) -> list[str]:
    now = datetime.now(timezone.utc)
    expired = [
        sid for sid, data in _store.items()
        if (now - data["last_activity"]).total_seconds() > max_idle_seconds
    ]
    for sid in expired:
        del _store[sid]
    return expired
