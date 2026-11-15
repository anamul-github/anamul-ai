"""Tests for reading Claude's reply. A fake client returns canned replies, so nothing calls the API."""

import json
from types import SimpleNamespace

import pytest

from anamul_ai import answer


@pytest.fixture
def claude_says(monkeypatch):
    """Make the fake Claude reply with this text (and stop reason) on the next call."""
    def set_reply(text, stop_reason="end_turn"):
        response = SimpleNamespace(stop_reason=stop_reason, content=[SimpleNamespace(type="text", text=text)])
        create = lambda **request: response
        client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=create)))
        monkeypatch.setattr(answer, "get_client", lambda: client)
        monkeypatch.setattr(answer, "get_settings", lambda: SimpleNamespace(claude_model="a-model"))
    return set_reply


def test_the_answer_and_its_used_sources_are_read_from_the_json(claude_says):
    claude_says(json.dumps({"answer": " I worked at OATI. ", "used_sources": [2, 1]}))
    reply = answer.write_answer("What did you do at OATI?", ["chunk one", "chunk two"])
    assert reply.text == "I worked at OATI."
    assert reply.used == [2, 1]


def test_source_ids_that_do_not_exist_and_repeats_are_ignored(claude_says):
    claude_says(json.dumps({"answer": "Hi!", "used_sources": [1, 1, 0, 7]}))
    assert answer.write_answer("hi", ["only chunk"]).used == [1]


def test_a_refusal_becomes_a_polite_reply_with_no_sources(claude_says):
    claude_says("", stop_reason="refusal")
    reply = answer.write_answer("something bad", ["chunk"])
    assert reply.text == "Sorry, I can't help with that one."
    assert reply.used == []


def test_a_reply_that_is_not_json_is_shown_as_it_is(claude_says):
    claude_says("Hi there!")
    reply = answer.write_answer("hi", [])
    assert reply.text == "Hi there!"
    assert reply.used == []
