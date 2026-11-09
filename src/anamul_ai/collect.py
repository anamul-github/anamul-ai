"""Download my articles and book notes from anamulhasan.com and save them as Markdown in data/.

Run: uv run python -m anamul_ai.collect
"""

from pathlib import Path

import httpx
from markdownify import markdownify

SITE = "https://www.anamulhasan.com"
DATA_DIR = Path("data")


def get_json(path: str):
    """GET a path from my site's API and return the parsed JSON."""
    response = httpx.get(f"{SITE}{path}", timeout=30)
    response.raise_for_status()  # Fail loudly on a 404 or 500 instead of saving an error page
    return response.json()


def to_markdown(html: str) -> str:
    """Convert the HTML that my site's editor saves into clean Markdown."""
    return markdownify(html, heading_style="ATX", strip=["img", "span"]).strip()


def front_matter(title: str, kind: str, url: str) -> str:
    """The header at the top of each file, so every answer can cite its source."""
    return f"---\ntitle: {title}\ntype: {kind}\nurl: {url}\n---"


def article_to_markdown(article: dict) -> str:
    url = f"{SITE}/articles/{article['slug']}"
    header = front_matter(article["title"], "article", url)
    meta = f"By {article['author']}, published {article['publishedDate']}. Category: {article['category']}\n\n"
    return header + f"\n\n# {article['title']}\n\n" + meta + to_markdown(article["content"])


def book_note_to_markdown(note: dict) -> str:
    url = f"{SITE}/book-notes/{note['slug']}"
    parts = [
        front_matter(f"{note['title']} (book notes)", "book-note", url),
        f"# {note['title']} by {note['bookAuthor']}",
        f"My rating: {note['rating']}/10. Read in {note['dateRead']}. Topics: {note['topics']}",
        "## The book in 3 sentences",
        "\n".join(f"- {sentence}" for sentence in note["bookIn3Sentences"]),
        "## My impressions",
        note["impressions"],
        "## Who should read it",
        note["whoShouldRead"],
        "## How the book changed me",
        "\n\n".join(note["howItChangedMe"]),
        "## My favorite quotes",
    ]
    for quote in note["topQuotes"]:
        # Some quotes start with a heading line, like "On overcoming fear\nThere is only one thing..."
        heading, _, text = quote.partition("\n")
        parts.append(f"> {text}\n\n({heading})" if text else f"> {heading}")
    parts += ["## My notes", to_markdown(note.get("notes", ""))]  # Some notes don't have this section yet
    return "\n\n".join(parts)


def save(folder: str, slug: str, text: str) -> None:
    path = DATA_DIR / folder / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")
    print(f"  saved {path} ({len(text.split())} words)")


def main() -> None:
    print("Articles:")
    for article in get_json("/api/articles"):
        save("articles", article["slug"], article_to_markdown(article))

    print("Book notes:")
    for summary in get_json("/api/book-notes"):
        # The list endpoint leaves out the long fields, so fetch each full note by its slug
        note = get_json(f"/api/book-notes/{summary['slug']}")
        save("book-notes", note["slug"], book_note_to_markdown(note))


if __name__ == "__main__":
    main()
