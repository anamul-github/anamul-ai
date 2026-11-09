"""Day 9: meaning fingerprints (embeddings) for every chunk, made with Voyage AI.

An embedding is a list of 1,024 numbers that captures what a text means.
Texts with similar meanings get similar numbers, even when they share no words,
so "Tell me about yourself" lands close to "Hello, I am Anamul Hasan, a curious learner...".
Run it with:  uv run python -m anamul_ai.embed
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
BATCH_SIZE = 30  # Chunks per request: about 5,000 tokens
# Without a payment method, Voyage allows only 10,000 tokens and 3 requests per minute,
# so the script rests between batches to stay under that limit
PAUSE_SECONDS = 60


@cache
def get_client() -> voyageai.Client:
    # max_retries: if Voyage says "too many requests", wait and try again instead of failing
    return voyageai.Client(api_key=get_settings().voyage_api_key.get_secret_value(), max_retries=5)


def embed_query(text: str) -> list[float]:
    """The meaning fingerprint of a visitor's question."""
    # input_type="query" tells Voyage this is a question to match against documents
    return get_client().embed([text], model=MODEL, input_type="query").embeddings[0]


def similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity: 1.0 means the same meaning, around 0 means unrelated.

    It compares the direction two lists of numbers point in, ignoring how long they are.
    """
    dot = sum(x * y for x, y in zip(a, b))  # zip pairs the numbers up, like a.map((x, i) => x * b[i])
    length_a = math.sqrt(sum(x * x for x in a))
    length_b = math.sqrt(sum(y * y for y in b))
    return dot / (length_a * length_b)


def load_embeddings() -> dict[str, list[float]]:
    """Chunk id -> fingerprint, or an empty dict if this script hasn't been run yet."""
    if not EMBEDDINGS_FILE.exists():
        return {}
    return json.loads(EMBEDDINGS_FILE.read_text(encoding="utf-8"))["vectors"]


def main() -> None:
    chunks = [json.loads(line) for line in CHUNKS_FILE.read_text(encoding="utf-8").splitlines()]
    vectors = {}
    total_tokens = 0
    for start in range(0, len(chunks), BATCH_SIZE):  # 0, 30, 60: like for (let i = 0; i < n; i += 30)
        if start > 0:
            print(f"  waiting {PAUSE_SECONDS} seconds for Voyage's per-minute limit...")
            time.sleep(PAUSE_SECONDS)  # Pause the program, like await new Promise(r => setTimeout(r, 60000))
        batch = chunks[start : start + BATCH_SIZE]
        # input_type="document": these are the texts that questions get matched against
        result = get_client().embed([chunk["text"] for chunk in batch], model=MODEL, input_type="document")
        for chunk, vector in zip(batch, result.embeddings):
            vectors[chunk["id"]] = vector
        total_tokens += result.total_tokens
        print(f"  embedded chunks {start + 1}-{start + len(batch)}")

    EMBEDDINGS_FILE.write_text(json.dumps({"model": MODEL, "vectors": vectors}), encoding="utf-8")
    dimensions = len(next(iter(vectors.values())))  # The length of the first fingerprint
    print(f"saved {EMBEDDINGS_FILE}: {len(vectors)} fingerprints of {dimensions} numbers each ({total_tokens} tokens)")


if __name__ == "__main__":
    main()
