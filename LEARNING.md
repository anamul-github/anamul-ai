# What I learned

## Day 1 (Nov 2): Python setup and basics
- `uv` manages Python versions, the virtual environment (`.venv`) and packages; `uv run` runs code inside the project's environment.
- Python vs JavaScript: no `let`/`const`, indentation instead of `{ }`, `def` instead of `function`, f-strings instead of template literals.
- Lists are arrays, dictionaries are objects; `len(x)` instead of `x.length`, `x in list` instead of `list.includes(x)`.

**My answer:** a list (`skills`) is ordered, so I get items by position, like `skills[0]`, which is like a JavaScript array. A dictionary (`degree`) stores key → value pairs, so I get items by name, like `degree["school"]`, which is like a JavaScript object.

## Day 2 (Nov 2): Collecting my data
- `uv add httpx markdownify` installs packages and records them in `pyproject.toml`, like `npm install` and `package.json`.
- `httpx.get()` is like `fetch()`. `raise_for_status()` stops on 404/500 errors instead of failing silently.
- Type hints (`path: str`) are like TypeScript types, but Python doesn't enforce them while running.
- A list comprehension (`f"- {s}" for s in items`) is like `items.map(s => ...)`. `dict.get("key", "")` is like `obj.key ?? ""`.
- `if __name__ == "__main__":` runs code only when the file is run directly, not when it's imported.
- `collect.py` fetches the book notes list first (to learn which ones exist), then each full note by slug, because the list leaves out the long notes. That's the same pattern my React site uses.
- Result: 5 articles and 1 book note (about 8,300 words) saved as Markdown in `data/`, each with its title and URL so the bot can cite sources.

## Day 3 (Nov 3): My profile data and chunks
- `data/profile/` now has my About page and my projects (copied from my site) and my resume.
- `resume.py` reads my resume PDF with `pypdf`. Its "layout" mode keeps each printed line together; the default mode put every word on its own line.
- The PDF stays on my computer. The script removes my phone number with a regular expression (`re`, like JavaScript's `/pattern/`) and refuses to save if one slips through, because this repo is public.
- `sys.argv` holds the command-line arguments, like `process.argv` in Node. A set (`{"SUMMARY", ...}`) is for fast "is it in here?" checks.
- `resume.py` reuses `front_matter` from `collect.py`. Importing it doesn't download anything, thanks to `if __name__ == "__main__":` from Day 2.
- `chunk.py` splits every file in `data/` at its headings, then packs paragraphs into chunks of at most 250 words. Result: 87 chunks, about 121 words each.
- `@dataclass` is like a TypeScript interface that is also a class. `with open(...)` closes the file automatically. `Path.rglob("*.md")` finds files in every folder. JSON Lines means one JSON object per line.
- `data/chunks.jsonl` isn't committed, because `uv run python -m anamul_ai.chunk` rebuilds it in a second.

**My answer (1):** We split data into chunks because it's cost effective: Claude gets fewer words with each question. The bot sends only the chunks that match the question, so the answer is focused instead of going over unrelated sources. Each chunk also carries its URL and section, so the answer can show where it came from.

**My answer (2):** Each chunk starts with where it came from (resume > Work experience > DevOps Engineer) because the bot finds and reads each chunk on its own. The header adds words like "OATI" and "DevOps Engineer" so the search can match the question, and it tells Claude whose work this is and in which role, so the answer is accurate.
