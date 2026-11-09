"""Day 4: my first API with FastAPI.

It serves the chunks from Day 3 over HTTP and has a simple keyword search,
a first version of how the bot will find the right chunks for a question.
Run it with:  uv run fastapi dev src/anamul_ai/api.py
Then open http://127.0.0.1:8000/docs to try every endpoint in the browser.
"""

import json
import re
from pathlib import Path

import anthropic
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field  # Pydantic checks that data has the right fields and types

from anamul_ai.answer import write_answer

CHUNKS_FILE = Path("data/chunks.jsonl")
WORD = re.compile(r"[a-z0-9]+")
# Words too common to tell chunks apart. Almost every chunk is about Anamul, so his name is here too.
STOP_WORDS = {
    "a", "about", "an", "and", "are", "at", "did", "do", "does", "for", "has", "have", "he", "his",
    "how", "i", "in", "is", "it", "me", "my", "of", "on", "or", "the", "to", "was", "what", "when",
    "where", "which", "who", "with", "anamul", "hasan",
    "you", "your", "yours", "yourself",  # Day 8: the bot speaks as Anamul, so visitors ask "you" and mean him
}

app = FastAPI(title="Anamul AI", description="Answers questions about Anamul Hasan, with sources.")


class Chunk(BaseModel):  # Like Day 3's dataclass, but FastAPI also uses it to check data and write the docs
    id: str
    title: str
    type: str
    url: str
    section: str
    text: str


class SearchResult(BaseModel):
    score: int  # How many of the question's words this chunk contains
    chunk: Chunk


def load_chunks() -> list[Chunk]:
    if not CHUNKS_FILE.exists():
        raise SystemExit(f"{CHUNKS_FILE} is missing. Run this first: uv run python -m anamul_ai.chunk")
    with CHUNKS_FILE.open(encoding="utf-8") as file:
        # Chunk(**row) is like new Chunk({...row}) in JavaScript: each key becomes a field
        return [Chunk(**json.loads(line)) for line in file]


def words(text: str) -> set[str]:
    """The distinct, meaningful words in a text, in lowercase."""
    return set(WORD.findall(text.lower())) - STOP_WORDS  # "-" on sets removes the stop words


CHUNKS = load_chunks()  # Read once when the server starts, not on every request


@app.get("/")  # A decorator: like app.get("/", handler) in Express, written above the function
def home() -> dict:
    return {"name": "Anamul AI", "chunks": len(CHUNKS), "docs": "/docs"}  # Returning a dict sends JSON, like res.json()


@app.get("/chunks")
def list_chunks(type: str | None = None) -> list[Chunk]:
    """All chunks, or only one type: article, book-note, resume, about or projects."""
    # `type: str | None = None` makes ?type= optional; FastAPI reads it from the URL for you
    if type is None:
        return CHUNKS
    return [chunk for chunk in CHUNKS if chunk.type == type]


@app.get("/chunks/{chunk_id}")
def get_chunk(chunk_id: str) -> Chunk:
    """One chunk by its id, like resume-3."""
    for chunk in CHUNKS:
        if chunk.id == chunk_id:
            return chunk
    raise HTTPException(status_code=404, detail=f"No chunk with id {chunk_id}")  # Like res.status(404).json(...)


@app.get("/search")
def search(q: str, limit: int = 5) -> list[SearchResult]:
    """Find the chunks that share the most words with the question.

    Keyword search only matches exact words, so "leader" won't find "led".
    In Week 2, embeddings will search by meaning instead.
    """
    question = words(q)
    results = []
    for chunk in CHUNKS:
        score = len(question & words(chunk.text))  # "&" on sets keeps only the words both have
        if score > 0:
            results.append(SearchResult(score=score, chunk=chunk))
    results.sort(key=lambda result: result.score, reverse=True)  # Highest score first, like .sort((a, b) => b.score - a.score)
    return results[:limit]  # The first `limit` results, like .slice(0, limit)


# --- Day 6: the endpoint the chat widget will call ---

class AskRequest(BaseModel):  # The JSON the widget sends: {"question": "..."}
    # Field() adds rules. FastAPI rejects anything outside them with a 422, before my code runs.
    # The 300-character limit also keeps each question cheap once Claude answers it in Week 2.
    question: str = Field(min_length=3, max_length=300)


class Source(BaseModel):  # Where an answer came from, so the widget can show a link
    title: str
    url: str
    section: str


class AskResponse(BaseModel):  # The JSON the widget gets back
    question: str
    answer: str
    sources: list[Source]


@app.post("/ask")  # POST, not GET: the question travels in the request body as JSON, like fetch(url, {method: "POST", body})
def ask(request: AskRequest) -> AskResponse:
    """Answer a question about Anamul, with sources.

    Day 8: Claude writes the answer from the matching chunks. The request and
    response shapes are the same as on Day 6, so the widget won't need to change.
    """
    results = search(request.question, limit=5)  # Reuse Day 4's search; a route is still a normal function
    if not results:
        # No matching chunks means nothing to answer from, so don't spend money asking Claude
        return AskResponse(question=request.question, answer="I couldn't find anything about that yet.", sources=[])

    try:
        answer = write_answer(request.question, [result.chunk.text for result in results])
    except anthropic.APIError:  # Claude busy, network down, rate limit...: tell the visitor kindly instead of crashing
        raise HTTPException(status_code=503, detail="The answer service is busy right now. Please try again in a minute.")

    sources = []
    for result in results:
        source = Source(title=result.chunk.title, url=result.chunk.url, section=result.chunk.section)
        if source not in sources:  # Two chunks from the same section would be the same source; list it once
            sources.append(source)
    return AskResponse(question=request.question, answer=answer, sources=sources)
