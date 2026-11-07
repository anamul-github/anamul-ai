"""Day 5: tests for api.py.

TestClient calls the API in memory, so no server needs to be running.
These tests read data/chunks.jsonl, so run `uv run python -m anamul_ai.chunk` first if it's missing.
Run them with:  uv run pytest
"""

from fastapi.testclient import TestClient

from anamul_ai.api import app

client = TestClient(app)  # Like a fake browser that sends requests straight to the app


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
