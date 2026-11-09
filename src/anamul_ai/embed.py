"""Embeddings for every chunk, made with Voyage AI, so search can work by meaning.

An embedding is a list of 1,024 numbers that captures what a text means: texts with
similar meanings are close even when they share no words.
Run: uv run python -m anamul_ai.embed
"""

import json
import math
import time
from functools import cache
from pathlib import Path

import voyageai

from anamul_ai.config import get_settings

CHUNKS_FILE = Path("data/chunks.jsonl")
EMBEDDINGS_FILE = Path("data/embeddings.json")
MODEL = "voyage-4"
BATCH_SIZE = 30  # About 5,000 tokens per request
# Without a payment method, Voyage allows 3 requests and 10,000 tokens per minute
PAUSE_SECONDS = 60


@cache
def get_client() -> voyageai.Client:
    # Retry on "too many requests" instead of failing right away
    return voyageai.Client(api_key=get_settings().voyage_api_key.get_secret_value(), max_retries=5)


def embed_query(text: str) -> list[float]:
    """The embedding of a visitor's question."""
    return get_client().embed([text], model=MODEL, input_type="query").embeddings[0]


def similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity: 1 means the same meaning, 0 unrelated, -1 opposite."""
    dot = sum(x * y for x, y in zip(a, b))
    length_a = math.sqrt(sum(x * x for x in a))
    length_b = math.sqrt(sum(y * y for y in b))
    return dot / (length_a * length_b)


def load_embeddings() -> dict[str, list[float]]:
    """Chunk id -> embedding, or {} if this script hasn't been run yet."""
    if not EMBEDDINGS_FILE.exists():
        return {}
    return json.loads(EMBEDDINGS_FILE.read_text(encoding="utf-8"))["vectors"]


def main() -> None:
    chunks = [json.loads(line) for line in CHUNKS_FILE.read_text(encoding="utf-8").splitlines()]
    vectors = {}
    total_tokens = 0
    for start in range(0, len(chunks), BATCH_SIZE):
        if start > 0:
            print(f"  waiting {PAUSE_SECONDS} seconds for Voyage's per-minute limit...")
            time.sleep(PAUSE_SECONDS)
        batch = chunks[start : start + BATCH_SIZE]
        # "document" for my chunks, "query" for questions: Voyage embeds each side for matching
        result = get_client().embed([chunk["text"] for chunk in batch], model=MODEL, input_type="document")
        for chunk, vector in zip(batch, result.embeddings):
            vectors[chunk["id"]] = vector
        total_tokens += result.total_tokens
        print(f"  embedded chunks {start + 1}-{start + len(batch)}")

    EMBEDDINGS_FILE.write_text(json.dumps({"model": MODEL, "vectors": vectors}), encoding="utf-8")
    dimensions = len(next(iter(vectors.values())))
    print(f"saved {EMBEDDINGS_FILE}: {len(vectors)} fingerprints of {dimensions} numbers each ({total_tokens} tokens)")


if __name__ == "__main__":
    main()
