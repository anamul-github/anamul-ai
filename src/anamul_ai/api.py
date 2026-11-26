"""The Anamul AI API: search my chunks and answer questions about me with Claude.

Run: uv run fastapi dev src/anamul_ai/api.py, then open http://127.0.0.1:8000/docs
"""

import json
import re
import time
from collections import defaultdict, deque
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

import anthropic
import voyageai
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from anamul_ai.answer import Answer, stream_answer, write_answer
from anamul_ai.chats import save_chat, save_feedback
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
# Keeps one visitor from running up my Claude bill. Counted per running server, which is enough for the beta.
MAX_QUESTIONS_PER_HOUR = 20
recent_questions: dict[str, deque] = defaultdict(deque)  # Visitor's IP address -> times of their questions

app = FastAPI(title="Anamul AI", description="Answers questions about Anamul Hasan, with sources.")

# Browsers only let these sites call the API: my website, its Vercel previews, and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.anamulhasan.com",
        "https://anamulhasan.com",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"https://my-website-git-[a-z0-9-]+-anamulgithubs-projects\.vercel\.app",
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


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

class Turn(BaseModel):  # One earlier message in the chat
    role: Literal["user", "assistant"]
    text: str = Field(max_length=1500)  # Answers are four sentences at most, so this is plenty


# The last three questions and answers: enough for "tell me more", and it keeps each question cheap
MAX_HISTORY = 6


class AskRequest(BaseModel):
    # At least 2 characters, so "hi" works; too long costs more per question and invites misuse
    question: str = Field(min_length=2, max_length=300)
    # The chat so far, oldest first, so follow-ups like "tell me more" make sense. The browser sends it.
    history: list[Turn] = Field(default=[], max_length=MAX_HISTORY)


class Source(BaseModel):  # A place the answer's facts came from, so the widget can link to it
    title: str
    url: str
    section: str


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[Source]
    chat_id: str | None = None  # For the thumbs up/down buttons; None when the chat wasn't saved


def check_rate_limit(visitor: str) -> None:
    """Allow MAX_QUESTIONS_PER_HOUR questions per visitor in any rolling hour, then answer 429."""
    now = time.time()
    times = recent_questions[visitor]
    while times and now - times[0] > 3600:  # Forget questions older than an hour
        times.popleft()
    if len(times) >= MAX_QUESTIONS_PER_HOUR:
        raise HTTPException(status_code=429, detail="You've asked a lot of questions! Please try again in a little while.")
    times.append(now)


def last_question(history: list[Turn]) -> str | None:
    """The visitor's previous question, if there was one."""
    for turn in reversed(history):
        if turn.role == "user":
            return turn.text
    return None


def search_text(question: str, history: list[Turn]) -> str:
    """What to search for. "Tell me more" alone finds nothing useful, so add the previous question to it."""
    previous = last_question(history)
    return f"{previous}\n{question}" if previous else question


BUSY = "The answer service is busy right now. Please try again in a minute."


def log_failure(service: str, error: Exception) -> None:
    """One JSON line per failed answer. CloudWatch counts these lines and emails me if they pile up."""
    print(json.dumps({"event": "answer_failed", "service": service, "error": type(error).__name__}), flush=True)


def visitor_ip(http: Request) -> str:
    """The visitor's IP address, for the rate limit.

    On Lambda, the web adapter forwards every request from inside the container, so the address
    the app sees is always the adapter's own. The real one is in the request details it passes along.
    """
    context = http.headers.get("x-amzn-request-context")
    if context:
        try:
            return json.loads(context)["http"]["sourceIp"]
        except (ValueError, KeyError, TypeError):
            pass
    return http.client.host if http.client else "unknown"


def find_sources(request: AskRequest, http: Request) -> list[SearchResult]:
    """The steps before Claude: check the rate limit, then search my chunks."""
    check_rate_limit(visitor_ip(http))
    try:
        return find_chunks(search_text(request.question, request.history))
    except voyageai.error.VoyageError as error:
        log_failure("voyage", error)
        # Voyage is down or rate-limited: a polite 503 instead of a crash
        raise HTTPException(status_code=503, detail=BUSY)


def finish(request: AskRequest, results: list[SearchResult], reply: Answer) -> AskResponse:
    """Keep only the sources Claude says it used (not everything search found), and save the chat."""
    sources = []
    for number in reply.used:
        chunk = results[number - 1].chunk
        source = Source(title=chunk.title, url=chunk.url, section=chunk.section)
        if source not in sources:  # Several chunks can come from one section; list it once
            sources.append(source)
    chat_id = save_chat(
        request.question, reply.text, [source.section for source in sources], last_question(request.history)
    )
    return AskResponse(question=request.question, answer=reply.text, sources=sources, chat_id=chat_id)


def history_pairs(request: AskRequest) -> list[tuple[str, str]]:
    return [(turn.role, turn.text) for turn in request.history]


@app.post("/ask")
def ask(request: AskRequest, http: Request) -> AskResponse:
    """Answer a question about me with Claude, using only the closest chunks, and return the sources."""
    results = find_sources(request, http)
    try:
        # With no close chunks, Claude can still greet or chat, but the system prompt stops it from stating facts
        reply = write_answer(request.question, [result.chunk.text for result in results], history_pairs(request))
    except anthropic.APIError as error:
        log_failure("claude", error)
        raise HTTPException(status_code=503, detail=BUSY)
    return finish(request, results, reply)


@app.post("/ask/stream")
def ask_stream(request: AskRequest, http: Request) -> StreamingResponse:
    """Like /ask, but sends the answer a few words at a time, so visitors see it being written.

    The reply is one JSON object per line: {"type": "text", "text": ...} for each new piece, then
    {"type": "done", ...} with the final answer and sources, or {"type": "error", "detail": ...}.
    """
    results = find_sources(request, http)  # Rate limit and search errors still get normal status codes

    def events() -> Iterator[str]:
        try:
            for item in stream_answer(request.question, [result.chunk.text for result in results], history_pairs(request)):
                if isinstance(item, Answer):
                    # The final answer replaces the streamed words, in case they differ (like after a refusal)
                    yield json.dumps({"type": "done", **finish(request, results, item).model_dump()}) + "\n"
                else:
                    yield json.dumps({"type": "text", "text": item}) + "\n"
        except anthropic.APIError as error:
            log_failure("claude", error)
            yield json.dumps({"type": "error", "detail": BUSY}) + "\n"

    return StreamingResponse(events(), media_type="application/x-ndjson")


class FeedbackRequest(BaseModel):
    chat_id: str = Field(pattern=r"^[0-9a-f]{32}$")  # The id /ask returned
    rating: Literal["up", "down"]


@app.post("/feedback")
def feedback(request: FeedbackRequest) -> dict:
    """A visitor's thumbs up or down on one answer, so I know which answers to improve."""
    if not save_feedback(request.chat_id, request.rating):
        raise HTTPException(status_code=404, detail="No saved chat with that id")
    return {"saved": True}
