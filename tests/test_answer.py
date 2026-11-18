"""Tests for reading Claude's reply. A fake client returns canned replies, so nothing calls the API."""

import json
from types import SimpleNamespace

import pytest

from anamul_ai import answer


@pytest.fixture
def claude_says(monkeypatch):
    """Make the fake Claude reply with this text (and stop reason) on the next call."""
    requests = []  # What was sent to the fake Claude

    def set_reply(text, stop_reason="end_turn"):
        response = SimpleNamespace(stop_reason=stop_reason, content=[SimpleNamespace(type="text", text=text)])
        create = lambda **request: requests.append(request) or response
        client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=create)))
        monkeypatch.setattr(answer, "get_client", lambda: client)
        monkeypatch.setattr(answer, "get_settings", lambda: SimpleNamespace(claude_model="a-model"))
        return requests
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


def test_the_chat_so_far_goes_in_my_message_as_a_quoted_conversation(claude_says):
    requests = claude_says(json.dumps({"answer": "More about OATI.", "used_sources": []}))
    history = [("user", "What did you do at OATI?"), ("assistant", "DevOps and web apps.")]
    answer.write_answer("Tell me more", ["chunk"], history)
    messages = requests[0]["messages"]
    assert len(messages) == 1 and messages[0]["role"] == "user"  # No made-up assistant turns
    assert "Visitor: What did you do at OATI?\nAnamul AI: DevOps and web apps." in messages[0]["content"]


def test_with_no_history_there_is_no_conversation_block(claude_says):
    requests = claude_says(json.dumps({"answer": "Hi!", "used_sources": []}))
    answer.write_answer("hi", [])
    assert "conversation_so_far" not in requests[0]["messages"][0]["content"]


def test_a_reply_that_is_not_json_is_shown_as_it_is(claude_says):
    claude_says("Hi there!")
    reply = answer.write_answer("hi", [])
    assert reply.text == "Hi there!"
    assert reply.used == []


def test_the_answer_is_read_from_half_written_json():
    assert answer.answer_so_far('{"answer": "I worked') == "I worked"
    assert answer.answer_so_far('{"answ') == ""
    assert answer.answer_so_far('{"answer": "Line one\\nLine two \\"quoted\\"", "used') == 'Line one\nLine two "quoted"'


def test_an_escape_is_held_back_until_it_has_fully_arrived():
    assert answer.answer_so_far('{"answer": "caf\\u00') == "caf"
    assert answer.answer_so_far('{"answer": "caf\\u00e9') == "café"


def test_streaming_yields_only_the_answer_words_then_the_answer(monkeypatch):
    pieces = ['{"ans', 'wer": "I wor', 'ked at OATI."', ', "used_sources": [1]}']
    final = SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text="".join(pieces))])

    class FakeStream:
        text_stream = iter(pieces)
        def __enter__(self): return self
        def __exit__(self, *error): return False
        def get_final_message(self): return final

    client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(stream=lambda **request: FakeStream())))
    monkeypatch.setattr(answer, "get_client", lambda: client)
    monkeypatch.setattr(answer, "get_settings", lambda: SimpleNamespace(claude_model="a-model"))
    items = list(answer.stream_answer("What did you do at OATI?", ["chunk"]))
    assert items[:-1] == ["I wor", "ked at OATI."]
    assert items[-1] == answer.Answer(text="I worked at OATI.", used=[1])
