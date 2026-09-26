"""Tests for the retry logic in app/llm.py (no real API calls)."""
import pytest

from app import llm


def test_retry_after_temporary_error(monkeypatch):
    calls = {"count": 0}

    def fake_call(prompt):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("503 UNAVAILABLE: the model is overloaded")
        return "ok"

    monkeypatch.setattr(llm, "call_chat_model", fake_call)
    monkeypatch.setattr(llm.time, "sleep", lambda seconds: None)  # do not really wait
    assert llm.generate_answer("hi") == "ok"
    assert calls["count"] == 2


def test_permanent_error_is_not_retried(monkeypatch):
    calls = {"count": 0}

    def fake_call(prompt):
        calls["count"] += 1
        raise RuntimeError("400 API key not valid")

    monkeypatch.setattr(llm, "call_chat_model", fake_call)
    with pytest.raises(RuntimeError):
        llm.generate_answer("hi")
    assert calls["count"] == 1


def test_gives_up_after_max_tries(monkeypatch):
    def fake_call(prompt):
        raise RuntimeError("503 UNAVAILABLE")

    monkeypatch.setattr(llm, "call_chat_model", fake_call)
    monkeypatch.setattr(llm.time, "sleep", lambda seconds: None)
    with pytest.raises(RuntimeError):
        llm.generate_answer("hi", max_tries=3)