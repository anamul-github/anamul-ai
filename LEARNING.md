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

## Day 4 (Nov 5): My first API with FastAPI
- An API lets other programs ask my project for data over the web. Later, the chat widget on my site will call this one.
- `uv add "fastapi[standard]"` installs FastAPI, and `uv run fastapi dev src/anamul_ai/api.py` runs a server that restarts whenever I save a file.
- `@app.get("/search")` above a function is like `app.get("/search", handler)` in Express. Returning a dict or a list sends JSON, like `res.json()`.
- Function parameters become URL inputs: `def search(q: str, limit: int = 5)` reads `?q=...&limit=5`. FastAPI rejects `limit=abc` with a 422 error on its own. `raise HTTPException(status_code=404)` is like `res.status(404)`.
- A Pydantic model (`class Chunk(BaseModel)`) describes the shape of the data, like a TypeScript interface. FastAPI uses it to check the data and to build the `/docs` page for free.
- Sets: `a & b` keeps the words both have, and `a - b` removes words.
- I tested keyword search with recruiter questions. "What did Anamul do at OATI?" worked, "Does he know cloud and DevOps?" half worked, and "Is he a good leader?" and "What does he like to do for fun?" missed completely.
- Keyword search counts filler words like "your" and "like" the same as important words, can't tell cloud storage from cloud computing, and breaks ties by file order instead of relevance.

**My answer (1):** The API receives a question over the web, scores every chunk by how many words match, and sends back the best-matching chunks as JSON.

**My answer (2):** "Is he a good leader?" missed because my resume says "led" and "onboarding support", not "leader". Keyword search only matches exact words, so it can't tell they mean the same thing. Searching by meaning (semantic search with embeddings, Week 2) would fix it.

## Day 5 (Nov 6): Tests with pytest
- `uv add --dev pytest` installs pytest as a development tool: I need it to build the project, but the bot doesn't need it to run. It's like `devDependencies` in `package.json`.
- pytest runs every function whose name starts with `test_` in `tests/`. `assert` means "this must be true, or the test fails". pytest is like Jest: `assert x == 5` is `expect(x).toBe(5)`, and `uv run pytest` is `npm test`.
- `TestClient` is a fake browser that calls the API in memory, so no server needs to be running.
- Test what matters, not numbers that will change: the home page test checks `chunks > 0`, not `== 87`, so it still passes when I add articles.
- `all(...)` is like `.every()` in JavaScript.
- I broke a test on purpose (404 changed to 200). The output showed the failing test's name, the exact line (`test_api.py:28`) and the real values (`assert 404 == 200`). Then I fixed it and saw `8 passed` again.
- Result: 8 tests for the chunker and the API, all passing in under a second.

**My answer (1):** A test checks that my code actually does what I wanted. It runs the code step by step, passes when everything works, and fails with an error showing what broke. That way I find problems in seconds, without checking by hand.

**My answer (2):** In Week 2, search by meaning will find answers like my hobbies, where keyword search returned unrelated articles. When we swap the search, the tests are a safety net: if they still pass, the rest of the API still works, and if something breaks, a test fails and shows me where.

## Day 6 (Nov 6): POST /ask, the endpoint the chat widget will call
- `POST /ask` takes `{"question": "..."}` and returns `{"question", "answer", "sources"}`. For now the answer is the best-matching chunk. In Week 2, Claude writes the answer from the same chunks, and the shape stays the same, so the widget won't need to change.
- `@app.post("/ask")` with `def ask(request: AskRequest)` reads the JSON body, like `req.body` in Express, but checks it against a Pydantic model first.
- `Field(min_length=3, max_length=300)` adds rules. Bad input gets a 422 with a clear message (`string_too_short`, `"String should have at least 3 characters"`) before my code runs.
- A route is still a normal function, so `/ask` reuses `search()` from Day 4.
- Pydantic models compare by their fields, so `if source not in sources` skips duplicate sources.
- Tests send a POST with `client.post("/ask", json={...})`. Now there are 12 tests, all passing.
- `fastapi dev` reloads when I save a file. My Day 4 server was still running, so a new one couldn't start ("Address already in use" on port 8000). `kill <process id>` stopped it. Next time: press Ctrl+C in the server's tab when I'm done.

**My answer (1):** `/search` is a GET because it only reads (looks up) chunks, with the question in the URL. `/ask` is a POST because the chat widget sends the visitor's question in the request body as JSON. The question goes to my API, and my API calls Claude, so my secret API key stays on my server, never in the browser.

**My answer (2):** A question under 3 characters, like "hi", is too short to answer. The 300-character maximum keeps each question cheap once Claude answers it, and stops people from pasting huge text or misusing the bot. A real recruiter question easily fits.
