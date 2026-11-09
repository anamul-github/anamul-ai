"""The Anamul AI API: search my chunks and answer questions about me with Claude.

Run: uv run fastapi dev src/anamul_ai/api.py, then open http://127.0.0.1:8000/docs
"""

import json
import re
from pathlib import Path

import anthropic
import voyageai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from anamul_ai.answer import write_answer
from anamul_ai.embed import embed_query, load_embeddings, similarity

CHUNKS_FILE = Path("data/chunks.jsonl")
WORD = re.compile(r"[a-z0-9]+")
# Too common to tell chunks apart. My name is in almost every chunk.
STOP_WORDS = {
    "a", "about", "an", "and", "are", "at", "did", "do", "does", "for", "has", "have", "he", "his",
    "how", "i", "in", "is", "it", "me", "my", "of", "on", "or", "the", "to", "was", "what", "when",
    "where", "which", "who", "with", "anamul", "hasan",
    "you", "your", "yours", "yourself",  # The bot speaks as me, so "you" means me
}

app = FastAPI(title="Anamul AI", description="Answers questions about Anamul Hasan, with sources.")


class Chunk(BaseModel):
    id: str
    title: str
    type: str
    url: str
    section: str
    text: str


class SearchResult(BaseModel):
    score: float  # Keyword search: words matched. Meaning search: similarity from 0 to 1.
    chunk: Chunk


def load_chunks() -> list[Chunk]:
    if not CHUNKS_FILE.exists():
        raise SystemExit(f"{CHUNKS_FILE} is missing. Run this first: uv run python -m anamul_ai.chunk")
    with CHUNKS_FILE.open(encoding="utf-8") as file:
        return [Chunk(**json.loads(line)) for line in file]


def words(text: str) -> set[str]:
    """The distinct, meaningful words in a text, in lowercase."""
    return set(WORD.findall(text.lower())) - STOP_WORDS


CHUNKS = load_chunks()  # Loaded once at startup, not on every request
VECTORS = load_embeddings()  # Chunk id -> embedding; empty until embed.py has run


@app.get("/")
def home() -> dict:
    return {"name": "Anamul AI", "chunks": len(CHUNKS), "docs": "/docs"}


@app.get("/chunks")
def list_chunks(type: str | None = None) -> list[Chunk]:
    """All chunks, or only one type: article, book-note, resume, about or projects."""
    if type is None:
        return CHUNKS
    return [chunk for chunk in CHUNKS if chunk.type == type]


@app.get("/chunks/{chunk_id}")
def get_chunk(chunk_id: str) -> Chunk:
    """One chunk by its id, like resume-3."""
    for chunk in CHUNKS:
        if chunk.id == chunk_id:
            return chunk
    raise HTTPException(status_code=404, detail=f"No chunk with id {chunk_id}")


@app.get("/search")
def search(q: str, limit: int = 5) -> list[SearchResult]:
    """Keyword search: the chunks that share the most words with the question.

    It only matches exact words ("leader" won't find "led"), so /ask uses meaning search instead.
    """
    question = words(q)
    results = []
    for chunk in CHUNKS:
        score = len(question & words(chunk.text))
        if score > 0:
            results.append(SearchResult(score=score, chunk=chunk))
    results.sort(key=lambda result: result.score, reverse=True)
    return results[:limit]


@app.get("/search/meaning")
def meaning_search(q: str, limit: int = 5) -> list[SearchResult]:
    """Meaning search: the chunks whose embeddings are closest to the question's, even with no shared words."""
    question = embed_query(q)
    results = [
        SearchResult(score=round(similarity(question, VECTORS[chunk.id]), 3), chunk=chunk)
        for chunk in CHUNKS
        if chunk.id in VECTORS
    ]
    results.sort(key=lambda result: result.score, reverse=True)
    return results[:limit]


# Measured: real questions scored 0.29 or more, nonsense like "xylophone zebra" about 0.13
MIN_SIMILARITY = 0.2


def find_chunks(question: str, limit: int = 5) -> list[SearchResult]:
    """Meaning search once the embeddings exist, otherwise keyword search."""
    if VECTORS:
        # Meaning search always returns something, so keep only the chunks that are really close
        return [result for result in meaning_search(question, limit) if result.score >= MIN_SIMILARITY]
    return search(question, limit)


# --- The endpoint the chat widget calls ---

class AskRequest(BaseModel):
    # Too short can't be answered; too long costs more per question and invites misuse
    question: str = Field(min_length=3, max_length=300)


class Source(BaseModel):  # Where an answer came from, so the widget can link to it
    title: str
    url: str
    section: str


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[Source]


@app.post("/ask")
def ask(request: AskRequest) -> AskResponse:
    """Answer a question about me with Claude, using only the closest chunks, and return the sources."""
    try:
        results = find_chunks(request.question)
        if not results:
            # Nothing to answer from, so skip the Claude call and its cost
            return AskResponse(question=request.question, answer="I couldn't find anything about that yet.", sources=[])
        answer = write_answer(request.question, [result.chunk.text for result in results])
    except (anthropic.APIError, voyageai.error.VoyageError):
        # Claude or Voyage is down or rate-limited: a polite 503 instead of a crash
        raise HTTPException(status_code=503, detail="The answer service is busy right now. Please try again in a minute.")

    sources = []
    for result in results:
        source = Source(title=result.chunk.title, url=result.chunk.url, section=result.chunk.section)
        if source not in sources:  # Several chunks can come from one section; list it once
            sources.append(source)
    return AskResponse(question=request.question, answer=answer, sources=sources)
