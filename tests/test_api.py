"""Tests for the API. They read data/chunks.jsonl (run anamul_ai.chunk first) and need no API keys."""

import pytest
from fastapi.testclient import TestClient

from anamul_ai.api import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def no_voyage(monkeypatch):
    """Never call Voyage in tests: with no embeddings loaded, /ask uses keyword search."""
    monkeypatch.setattr("anamul_ai.api.VECTORS", {})


@pytest.fixture
def fake_claude(monkeypatch):
    """Replace Claude with a fake, so tests are free, fast and predictable. Returns the calls it got."""
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
    # My articles say "you" a lot; before this fix they pushed my OATI job out of the results
    results = client.get("/search", params={"q": "What did you do at OATI?"}).json()
    assert len(results) > 0
    assert all(result["chunk"]["type"] == "resume" for result in results)


# --- POST /ask ---

def test_ask_returns_an_answer_with_sources(fake_claude):
    response = client.post("/ask", json={"question": "What did Anamul do at OATI?"})
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "A fake answer."
    assert body["sources"][0]["url"] == "https://www.linkedin.com/in/anamul-hasan"  # OATI is on my resume


def test_ask_sends_claude_the_matching_chunks(fake_claude):
    client.post("/ask", json={"question": "What did Anamul do at OATI?"})
    assert len(fake_claude) == 1
    assert fake_claude[0]["question"] == "What did Anamul do at OATI?"
    assert any("OATI" in source for source in fake_claude[0]["sources"])


def test_ask_rejects_a_question_that_is_too_short():
    assert client.post("/ask", json={"question": "hi"}).status_code == 422


def test_ask_rejects_a_question_that_is_too_long():
    assert client.post("/ask", json={"question": "why " * 100}).status_code == 422  # 400 characters, over the 300 limit


def test_ask_says_so_when_nothing_matches(fake_claude):
    body = client.post("/ask", json={"question": "xylophone zebra"}).json()
    assert body["sources"] == []
    assert fake_claude == []  # Nothing to answer from, so no Claude call


# --- Search by meaning ---

def test_meaning_search_puts_the_closest_meaning_first(monkeypatch):
    # Tiny 2-number embeddings and a fake Voyage
    monkeypatch.setattr("anamul_ai.api.VECTORS", {"resume-3": [1.0, 0.0], "about-3": [0.0, 1.0]})
    monkeypatch.setattr("anamul_ai.api.embed_query", lambda text: [0.9, 0.1])
    results = client.get("/search/meaning", params={"q": "anything"}).json()
    assert [result["chunk"]["id"] for result in results] == ["resume-3", "about-3"]  # [0.9, 0.1] points almost like [1, 0]


def test_ask_skips_claude_when_nothing_is_close_in_meaning(monkeypatch, fake_claude):
    monkeypatch.setattr("anamul_ai.api.VECTORS", {"resume-3": [1.0, 0.0]})
    monkeypatch.setattr("anamul_ai.api.embed_query", lambda text: [0.0, 1.0])  # At a right angle: similarity 0
    body = client.post("/ask", json={"question": "xylophone zebra"}).json()
    assert body["sources"] == []
    assert fake_claude == []  # Below MIN_SIMILARITY, so no Claude call


# --- CORS: which websites may call the API from a browser ---

def test_my_website_may_call_the_api():
    response = client.get("/", headers={"Origin": "https://www.anamulhasan.com"})
    assert response.headers["access-control-allow-origin"] == "https://www.anamulhasan.com"


def test_other_websites_may_not():
    response = client.get("/", headers={"Origin": "https://example.com"})
    assert "access-control-allow-origin" not in response.headers
