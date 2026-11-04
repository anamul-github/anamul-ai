"""Day 3: split everything in data/ into small chunks the chatbot can search.

The bot can't send all of data/ to Claude with every question, so it will look up
the few pieces that match the question. Those pieces are chunks: one section of a
file, small enough to be about one thing, with its title and URL for citing.
Run it with:  uv run python -m anamul_ai.chunk
"""

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

DATA_DIR = Path("data")
OUTPUT = DATA_DIR / "chunks.jsonl"
MAX_WORDS = 250  # Big enough to keep a thought together, small enough to be about one thing
HEADING = re.compile(r"^(#{1,6})\s+(.*)")  # A Markdown heading: 1 to 6 #'s, a space, then the text


@dataclass  # Like a TypeScript interface that is also a class: fixed fields, and it writes __init__ for you
class Chunk:
    id: str
    title: str
    type: str
    url: str
    section: str
    text: str


def split_front_matter(text: str) -> tuple[dict, str]:
    """Separate the --- header that collect.py wrote from the rest. Returns (metadata, body)."""
    _, header, body = text.split("---\n", 2)  # At most 2 splits, so a --- later in the body is left alone
    meta = {}
    for line in header.splitlines():
        key, _, value = line.partition(": ")
        meta[key] = value
    return meta, body


def split_sections(body: str) -> list[tuple[str, str]]:
    """Split Markdown at its headings. Returns (heading path, text) pairs.

    The heading path is every heading above the text, like "Work experience > DevOps Engineer",
    so a chunk still makes sense when it's read on its own.
    """
    sections = []
    headings = {}  # Heading level -> heading text, for the headings above the current line
    lines = []
    for line in body.splitlines():
        match = HEADING.match(line)
        if not match:
            lines.append(line)
            continue
        sections.append((" > ".join(headings.values()), "\n".join(lines)))  # Save the section that just ended
        level, text = len(match[1]), match[2].strip().rstrip(":")
        # A new heading replaces any heading at its level or deeper, like a new chapter ends the old sections
        headings = {lvl: heading for lvl, heading in headings.items() if lvl < level}
        if level > 1:  # Level 1 is the page title, which every chunk already has
            headings[level] = text
        lines = []
    sections.append((" > ".join(headings.values()), "\n".join(lines)))
    return [(path, text.strip()) for path, text in sections if text.strip()]  # Skip headings with nothing under them


def pack(paragraphs: list[str]) -> list[str]:
    """Group paragraphs into pieces of at most MAX_WORDS words, without cutting a paragraph in half."""
    pieces, current = [], []
    for paragraph in paragraphs:
        if current and len(" ".join(current + [paragraph]).split()) > MAX_WORDS:
            pieces.append("\n\n".join(current))
            current = []
        current.append(paragraph)
    if current:
        pieces.append("\n\n".join(current))
    return pieces


def chunk_file(file: Path) -> list[Chunk]:
    meta, body = split_front_matter(file.read_text(encoding="utf-8"))
    chunks = []
    for section, text in split_sections(body):
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        for piece in pack(paragraphs):
            where = f"{meta['title']} > {section}" if section else meta["title"]
            chunks.append(Chunk(
                id=f"{file.stem}-{len(chunks) + 1}",
                title=meta["title"],
                type=meta["type"],
                url=meta["url"],
                section=section,
                text=f"{where}\n\n{piece}",  # Starts with where it came from, so the search and Claude both see it
            ))
    print(f"  {file}: {len(chunks)} chunks")
    return chunks


def main() -> None:
    chunks = []
    for file in sorted(DATA_DIR.rglob("*.md")):  # rglob searches every folder inside data/
        chunks += chunk_file(file)

    # JSON Lines: one JSON object per line, so later steps can read it one chunk at a time
    with OUTPUT.open("w", encoding="utf-8") as out:  # "with" closes the file when the block ends
        for chunk in chunks:
            out.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")

    sizes = [len(chunk.text.split()) for chunk in chunks]
    print(f"saved {OUTPUT}: {len(chunks)} chunks, average {sum(sizes) // len(sizes)} words, largest {max(sizes)}")


if __name__ == "__main__":
    main()
