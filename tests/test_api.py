"""Day 5: tests for api.py.

TestClient calls the API in memory, so no server needs to be running.
These tests read data/chunks.jsonl, so run `uv run python -m anamul_ai.chunk` first if it's missing.
Run them with:  uv run pytest
"""

import pytest
from fastapi.testclient import TestClient

from anamul_ai.api import app

client = TestClient(app)  # Like a fake browser that sends requests straight to the app


@pytest.fixture(autouse=True)  # autouse: every test in this file gets it, without asking for it
def no_voyage(monkeypatch):
    """Day 9: tests never call Voyage. With no fingerprints loaded, /ask falls back to keyword search."""
    monkeypatch.setattr("anamul_ai.api.VECTORS", {})


@pytest.fixture  # A fixture is setup that a test asks for by naming it as a parameter
def fake_claude(monkeypatch):
    """Day 8: swap the real Claude call for a fake one, so tests are free, fast and need no API key.

    monkeypatch puts the real write_answer back when the test ends.
    Returns a list that records every question the fake was asked.
    """
    calls = []

    def fake_write_answer(question, sources):
        calls.append({"question": question, "sources": sources})
        return "A fake answer."

    monkeypatch.setattr("anamul_ai.api.write_answer", fake_write_answer)
    return calls


def test_home_says_how_many_chunks_there_are():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["chunks"] > 0


def test_chunks_can_be_filtered_by_type():
    chunks = client.get("/chunks", params={"type": "resume"}).json()
    assert len(chunks) > 0
    assert all(chunk["type"] == "resume" for chunk in chunks)


def test_unknown_chunk_is_a_404():
    assert client.get("/chunks/does-not-exist").status_code == 404


def test_limit_must_be_a_number():
    assert client.get("/search", params={"q": "OATI", "limit": "abc"}).status_code == 422


def test_search_finds_my_oati_job():
    results = client.get("/search", params={"q": "What did Anamul do at OATI?"}).json()
    assert len(results) > 0
    assert all(result["chunk"]["type"] == "resume" for result in results)


def test_search_ignores_you_because_visitors_mean_me():
    # Day 8: the bot speaks as me, so "you" means Anamul. My articles say "you" a lot,
    # and before this fix they pushed my OATI job out of the results completely.
    results = client.get("/search", params={"q": "What did you do at OATI?"}).json()
    assert len(results) > 0
    assert all(result["chunk"]["type"] == "resume" for result in results)


# --- Day 6: POST /ask ---

def test_ask_returns_an_answer_with_sources(fake_claude):
    response = client.post("/ask", json={"question": "What did Anamul do at OATI?"})  # json= sends a request body
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "A fake answer."  # The answer comes from (fake) Claude
    assert body["sources"][0]["url"] == "https://www.linkedin.com/in/anamul-hasan"  # OATI is on my resume


def test_ask_sends_claude_the_matching_chunks(fake_claude):
    client.post("/ask", json={"question": "What did Anamul do at OATI?"})
    assert len(fake_claude) == 1  # Claude was asked exactly once
    assert fake_claude[0]["question"] == "What did Anamul do at OATI?"
    assert any("OATI" in source for source in fake_claude[0]["sources"])  # any() is like .some() in JavaScript


def test_ask_rejects_a_question_that_is_too_short():
    assert client.post("/ask", json={"question": "hi"}).status_code == 422


def test_ask_rejects_a_question_that_is_too_long():
    assert client.post("/ask", json={"question": "why " * 100}).status_code == 422  # 400 characters, over the 300 limit


def test_ask_says_so_when_nothing_matches(fake_claude):
    body = client.post("/ask", json={"question": "xylophone zebra"}).json()
    assert body["sources"] == []
    assert fake_claude == []  # Nothing to answer from, so Claude wasn't asked (and nothing was spent)


# --- Day 9: search by meaning ---

def test_meaning_search_puts_the_closest_meaning_first(monkeypatch):
    # Tiny made-up fingerprints with 2 numbers instead of 1,024, and a fake Voyage
    monkeypatch.setattr("anamul_ai.api.VECTORS", {"resume-3": [1.0, 0.0], "about-3": [0.0, 1.0]})
    monkeypatch.setattr("anamul_ai.api.embed_query", lambda text: [0.9, 0.1])  # lambda: a one-line function, like text => [0.9, 0.1]
    results = client.get("/search/meaning", params={"q": "anything"}).json()
    assert [result["chunk"]["id"] for result in results] == ["resume-3", "about-3"]  # [0.9, 0.1] points almost the same way as [1, 0]


def test_ask_skips_claude_when_nothing_is_close_in_meaning(monkeypatch, fake_claude):
    monkeypatch.setattr("anamul_ai.api.VECTORS", {"resume-3": [1.0, 0.0]})
    monkeypatch.setattr("anamul_ai.api.embed_query", lambda text: [0.0, 1.0])  # At a right angle: similarity 0
    body = client.post("/ask", json={"question": "xylophone zebra"}).json()
    assert body["sources"] == []
    assert fake_claude == []  # Below MIN_SIMILARITY, so Claude wasn't asked
