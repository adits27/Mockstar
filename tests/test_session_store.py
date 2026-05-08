import pytest
from app.store import session_store


@pytest.fixture(autouse=True)
def clear_store():
    session_store.clear()
    yield
    session_store.clear()


def test_create_and_get_session():
    session_store.create("sess-1", user_profile={"experience_level": "junior"}, metadata={"job_role": "SWE"})
    session = session_store.get("sess-1")
    assert session is not None
    assert session["metadata"]["job_role"] == "SWE"
    assert session["turns"] == []


def test_get_nonexistent_session_returns_none():
    assert session_store.get("missing") is None


def test_add_turn_appends_to_session():
    session_store.create("sess-2", user_profile={}, metadata={})
    session_store.add_turn("sess-2", {"turn_index": 0, "transcript": "Hello world", "filler_words": {}, "pause_count": 0, "wpm": 120.0})
    session = session_store.get("sess-2")
    assert len(session["turns"]) == 1
    assert session["turns"][0]["transcript"] == "Hello world"


def test_update_turn_metrics():
    session_store.create("sess-3", user_profile={}, metadata={})
    session_store.add_turn("sess-3", {"turn_index": 0, "transcript": "Um hello", "filler_words": {}, "pause_count": 0, "wpm": None})
    session_store.update_turn_metrics("sess-3", turn_index=0, filler_words={"um": 1}, pause_count=0, wpm=95.0)
    turn = session_store.get("sess-3")["turns"][0]
    assert turn["filler_words"] == {"um": 1}
    assert turn["wpm"] == 95.0


def test_delete_session():
    session_store.create("sess-4", user_profile={}, metadata={})
    session_store.delete("sess-4")
    assert session_store.get("sess-4") is None
