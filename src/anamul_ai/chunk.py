"""Split everything in data/ into small chunks for search, saved to data/chunks.jsonl.

Each chunk is one section of a file, with its title and URL so answers can cite it.
Run: uv run python -m anamul_ai.chunk
"""

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

DATA_DIR = Path("data")
OUTPUT = DATA_DIR / "chunks.jsonl"
MAX_WORDS = 250  # Big enough to keep a thought together, small enough to be about one thing
HEADING = re.compile(r"^(#{1,6})\s+(.*)")  # A Markdown heading line


@dataclass
class Chunk:
    id: str
    title: str
    type: str
    url: str
    section: str
    text: str


def split_front_matter(text: str) -> tuple[dict, str]:
    """Separate the --- header from the body. Returns (metadata, body)."""
    _, header, body = text.split("---\n", 2)  # At most 2 splits, so a --- inside the body stays put
    meta = {}
    for line in header.splitlines():
        key, _, value = line.partition(": ")
        meta[key] = value
    return meta, body


def split_sections(body: str) -> list[tuple[str, str]]:
    """Split Markdown at its headings. Returns (heading path, text) pairs.

    The heading path, like "Work experience > DevOps Engineer", keeps each chunk understandable on its own.
    """
    sections = []
    headings = {}  # Heading level -> text, for the headings above the current line
    lines = []
    for line in body.splitlines():
        match = HEADING.match(line)
        if not match:
            lines.append(line)
            continue
        sections.append((" > ".join(headings.values()), "\n".join(lines)))  # Close the section that just ended
        level, text = len(match[1]), match[2].strip().rstrip(":")
        # A new heading replaces any heading at its level or deeper
        headings = {lvl: heading for lvl, heading in headings.items() if lvl < level}
        if level > 1:  # Level 1 is the page title, already in every chunk
            headings[level] = text
        lines = []
    sections.append((" > ".join(headings.values()), "\n".join(lines)))
    return [(path, text.strip()) for path, text in sections if text.strip()]  # Skip headings with nothing under them


def pack(paragraphs: list[str]) -> list[str]:
    """Group paragraphs into pieces of at most MAX_WORDS words, without splitting a paragraph."""
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
                text=f"{where}\n\n{piece}",  # Starts with where it came from, so search and Claude both see it
            ))
    print(f"  {file}: {len(chunks)} chunks")
    return chunks


def main() -> None:
    chunks = []
    for file in sorted(DATA_DIR.rglob("*.md")):
        chunks += chunk_file(file)

    with OUTPUT.open("w", encoding="utf-8") as out:  # JSON Lines: one chunk per line
        for chunk in chunks:
            out.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")

    sizes = [len(chunk.text.split()) for chunk in chunks]
    print(f"saved {OUTPUT}: {len(chunks)} chunks, average {sum(sizes) // len(sizes)} words, largest {max(sizes)}")


if __name__ == "__main__":
    main()
