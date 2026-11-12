"""Tests for the API. They read data/chunks.jsonl (run anamul_ai.chunk first) and need no API keys."""

import pytest
from fastapi.testclient import TestClient

from anamul_ai.api import MAX_QUESTIONS_PER_HOUR, app, recent_questions

client = TestClient(app)


@pytest.fixture(autouse=True)
def no_voyage(monkeypatch):
    """Never call Voyage in tests: with no embeddings loaded, /ask uses keyword search."""
    monkeypatch.setattr("anamul_ai.api.VECTORS", {})


@pytest.fixture(autouse=True)
def fresh_rate_limit():
    """Each test starts with no questions counted, so tests don't use up each other's limit."""
    recent_questions.clear()


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
    assert all("OATI" in result["chunk"]["text"] for result in results)


def test_search_ignores_you_because_visitors_mean_me():
    # My articles say "you" a lot; before this fix they pushed my OATI job out of the results
    results = client.get("/search", params={"q": "What did you do at OATI?"}).json()
    assert len(results) > 0
    assert all("OATI" in result["chunk"]["text"] for result in results)


# --- POST /ask ---

def test_ask_returns_an_answer_with_sources(fake_claude):
    response = client.post("/ask", json={"question": "What did Anamul do at OATI?"})
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "A fake answer."
    assert body["sources"][0]["title"] in {"Anamul Hasan's resume", "About Anamul Hasan, in depth"}  # Both cover OATI


def test_ask_sends_claude_the_matching_chunks(fake_claude):
    client.post("/ask", json={"question": "What did Anamul do at OATI?"})
    assert len(fake_claude) == 1
    assert fake_claude[0]["question"] == "What did Anamul do at OATI?"
    assert any("OATI" in source for source in fake_claude[0]["sources"])


def test_ask_rejects_a_question_that_is_too_short():
    assert client.post("/ask", json={"question": "a"}).status_code == 422


def test_ask_accepts_hi(fake_claude):
    assert client.post("/ask", json={"question": "hi"}).status_code != 422


def test_ask_rejects_a_question_that_is_too_long():
    assert client.post("/ask", json={"question": "why " * 100}).status_code == 422  # 400 characters, over the 300 limit


def test_ask_still_chats_when_nothing_matches(fake_claude):
    body = client.post("/ask", json={"question": "xylophone zebra"}).json()
    assert body["sources"] == []
    assert fake_claude[0]["sources"] == []  # Claude can greet or chat, with no facts to use


# --- Search by meaning ---

def test_meaning_search_puts_the_closest_meaning_first(monkeypatch):
    # Tiny 2-number embeddings and a fake Voyage
    monkeypatch.setattr("anamul_ai.api.VECTORS", {"resume-3": [1.0, 0.0], "about-3": [0.0, 1.0]})
    monkeypatch.setattr("anamul_ai.api.embed_query", lambda text: [0.9, 0.1])
    results = client.get("/search/meaning", params={"q": "anything"}).json()
    assert [result["chunk"]["id"] for result in results] == ["resume-3", "about-3"]  # [0.9, 0.1] points almost like [1, 0]


def test_ask_sends_no_sources_when_nothing_is_close_in_meaning(monkeypatch, fake_claude):
    monkeypatch.setattr("anamul_ai.api.VECTORS", {"resume-3": [1.0, 0.0]})
    monkeypatch.setattr("anamul_ai.api.embed_query", lambda text: [0.0, 1.0])  # At a right angle: similarity 0
    body = client.post("/ask", json={"question": "xylophone zebra"}).json()
    assert body["sources"] == []
    assert fake_claude[0]["sources"] == []  # Below MIN_SIMILARITY, so Claude gets no chunks


# --- CORS: which websites may call the API from a browser ---

def test_my_website_may_call_the_api():
    response = client.get("/", headers={"Origin": "https://www.anamulhasan.com"})
    assert response.headers["access-control-allow-origin"] == "https://www.anamulhasan.com"


def test_other_websites_may_not():
    response = client.get("/", headers={"Origin": "https://example.com"})
    assert "access-control-allow-origin" not in response.headers


# --- Question limit per visitor ---

def test_a_visitor_is_limited_after_too_many_questions(fake_claude):
    for _ in range(MAX_QUESTIONS_PER_HOUR):
        assert client.post("/ask", json={"question": "hi"}).status_code == 200
    response = client.post("/ask", json={"question": "hi"})
    assert response.status_code == 429
    assert len(fake_claude) == MAX_QUESTIONS_PER_HOUR  # The extra question never reached Claude


def test_ask_returns_the_chat_id_when_the_chat_is_saved(monkeypatch, fake_claude):
    monkeypatch.setattr("anamul_ai.api.save_chat", lambda question, answer, sources: "a" * 32)
    response = client.post("/ask", json={"question": "What did you do at OATI?"})
    assert response.json()["chat_id"] == "a" * 32


def test_ask_still_answers_when_the_chat_is_not_saved(fake_claude):
    response = client.post("/ask", json={"question": "What did you do at OATI?"})
    assert response.json()["answer"] == "A fake answer."
    assert response.json()["chat_id"] is None


def test_feedback_must_be_up_or_down():
    response = client.post("/feedback", json={"chat_id": "a" * 32, "rating": "meh"})
    assert response.status_code == 422


def test_feedback_for_an_unknown_chat_is_a_404(monkeypatch):
    monkeypatch.setattr("anamul_ai.api.save_feedback", lambda chat_id, rating: False)
    response = client.post("/feedback", json={"chat_id": "a" * 32, "rating": "up"})
    assert response.status_code == 404


def test_feedback_is_saved(monkeypatch):
    saved = []
    monkeypatch.setattr("anamul_ai.api.save_feedback", lambda chat_id, rating: saved.append(rating) or True)
    response = client.post("/feedback", json={"chat_id": "a" * 32, "rating": "down"})
    assert response.status_code == 200
    assert saved == ["down"]
