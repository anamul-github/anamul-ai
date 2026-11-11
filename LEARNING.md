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

## Day 7 (Nov 8): My first message to Claude
- I created a Claude API key at platform.claude.com. My Max plan includes $100 a month in API credits, and I added no card, so I can't be charged by accident. The key expires on Feb 16, 2027, and its scope can't change my account settings.
- Secrets live in `.env`, which `.gitignore` keeps off GitHub. `.env.example` is committed and shows the format with a placeholder. `cp .env.example .env` replaces `.env` every time, so I run it only once.
- `pydantic-settings`: `class Settings(BaseSettings)` fills its fields from `.env`. `SecretStr` prints `**********` instead of the key, and `.get_secret_value()` unwraps it only when it's needed.
- `client.beta.messages.create(model=..., max_tokens=..., messages=[...])` sends a message. The reply is a list of blocks, and the answer is in the blocks with `type == "text"`.
- `output_config={"effort": "low"}` keeps simple questions cheap. `fallbacks="default"` retries on another model if a safety check declines a request.
- Friendly errors: catching `ValidationError` (missing key) and `anthropic.AuthenticationError` (wrong key) prints one clear line instead of a long traceback.
- First hello: 41 tokens in, 155 out, $0.00326. That's about 30,000 questions like it for $100.

**My answer (1):** My API key lives in `.env` because `.gitignore` keeps that file off GitHub, so nobody can see or steal the key and run up charges on my account. If a key is ever committed, deleting it later doesn't help, because it stays in the git history. `.env.example` shows which settings exist, without the real values.

**My answer (2):** Tokens are the pieces of text (about ¾ of a word each) that Claude reads as input and writes as output. I pay for every token, and output costs 5 times more than input on Opus 5.5. That's why the bot sends only the few matching chunks, and why I'll limit how much each visitor can ask.

## Day 8 (Nov 9): Claude writes the answers
- `/ask` now works like a real RAG bot: keyword search finds the 5 best chunks, Claude writes a two-to-four sentence answer from them, and the answer comes back with its sources. If nothing matches, it doesn't call Claude at all, so it costs nothing.
- I chose Claude Opus 5.5 (the best answers, about 1–2 cents per question) and the first person: the bot speaks as me, and says it's an AI assistant if someone asks.
- The system prompt (`SYSTEM_PROMPT` in `answer.py`) goes in `system=`. The chunks go in the user message inside `<source>` tags, so Claude can tell them apart.
- `@cache` creates the settings and the Claude client once and then reuses them, like a memoized function.
- `except anthropic.APIError` turns a Claude outage into a polite 503 ("try again in a minute") instead of a crash.
- The tests use a pytest fixture, `fake_claude`, which uses `monkeypatch` to swap `write_answer` for a fake. All 14 tests pass even with no API key.
- Bug found and fixed: since the bot speaks as me, visitors ask "you". My articles say "you" a lot, so "What did you do at OATI?" found zero OATI chunks. Adding "you" and "your" to the stop words fixed it, and a test guards it.
- Real answers: "What did you do at OATI?" and "What are your hobbies?" were accurate, in my voice, from my resume and About page. "What are you good at?" got the wrong chunks, and Claude honestly said it didn't know instead of inventing skills. "Tell me about yourself?" found no chunks at all.
- The answer can only be as good as the chunks search finds. Claude is ready; search is the weak link, so search by meaning is next.

**My answer (1):** The system prompt is Claude's standing instructions: who it is (me, speaking in the first person), how to answer (short and humble), and the rules. "Use only the sources" means Claude answers only from the chunks search found, without guessing. When the chunks didn't cover "What are you good at?", it said so instead of making up skills.

**My answer (2):** The tests check my code, not Claude, so they use a fake Claude. The real one would cost money on every test run, take seconds per answer, need my API key (which must never be on GitHub), and word its answer differently each time. The fake is free, instant and always gives the same answer.

## Day 9 (Nov 9): Search by meaning
- An embedding is a "meaning fingerprint": a list of 1,024 numbers that captures what a text means. Voyage AI's `voyage-4` model made one for each of my 87 chunks (13,765 tokens, covered by free tokens). `embed.py` saves them in `data/embeddings.json`, which isn't committed because it can always be rebuilt.
- Chunks are embedded with `input_type="document"` and questions with `input_type="query"`.
- Cosine similarity compares two fingerprints: 1 means the same meaning, 0 unrelated, -1 opposite. `similarity()` uses `zip`, `sum` and `math.sqrt`, and the tests use `pytest.approx` because decimals can be off by a tiny bit.
- Without a payment method, Voyage allows only 3 requests and 10,000 tokens per minute. My first run failed after 30 chunks, so the script now pauses 60 seconds between batches. Until I add a card (the free tokens still apply), the bot can answer about 3 questions a minute.
- `MIN_SIMILARITY = 0.2`, chosen by measuring: real questions scored 0.29 or more, and "xylophone zebra" only 0.13. Meaning search always returns something, so `/ask` drops chunks under 0.2 and skips Claude when nothing is left.
- `GET /search/meaning` shows the closest chunks and their scores. `/ask` now searches by meaning, and falls back to keyword search if the fingerprints don't exist yet.
- Before and after: "Tell me about yourself?" went from nothing to a full introduction from my About page. "What do you like to do for fun?" and "Does he know cloud and DevOps?" now find the right chunks. "Are you a good leader?" still misses my resume (rank 49 of 87).
- More tests in the browser: it refused to write a cat poem (prompt injection), said it's an AI when asked if it's the real me, didn't know my phone number (removed on Day 3), and was honest that Kubernetes isn't in my background.
- Problems found: "Why should we hire you?" said "I work full time" (from an older article, so it's out of date) and left out my technical skills. The weakness answer used a self-doubt story I may not want recruiters to see.
- 19 tests, all passing without any API keys.

**My answer (1):** An embedding is a "meaning fingerprint": a list of 1,024 numbers that represents what a text means. Meaning search turns the question into a fingerprint and finds the chunks with the closest fingerprints. "Tell me about yourself?" shares no important words with my About page, but their meanings are close, so meaning search found it when keyword search found nothing.

**My answer (2):** Each chunk gets one fingerprint for its whole text. My OATI DevOps chunk is mostly about infrastructure (Ansible, CI/CD, servers), and only 2 of its 8 bullets are about leading, so its fingerprint means "DevOps work" and the leadership gets drowned out, like strawberries in a banana smoothie. Smaller chunks would give leadership its own fingerprint.

## Day 10 (Nov 9): Anamul AI on my website
- I decided to launch a beta early, for anyone to chat with for fun, and revised the plan for the rest of November.
- On my website (React, branch `feat/anamul-ai-chat`): a `/chat` page, a floating chat bubble on every other page, and the header's Coffee Chat button is now "Anamul AI · Beta". The Coffee Chat page stays, linked from the chat page, article footers and contact cards.
- The website calls `POST /ask` with axios, shows "thinking" dots while it waits, and turns errors (busy, offline, too short) into friendly messages.
- The subtitle says "My AI avatar. Ask me anything about my work, projects and life." It doesn't claim the bot is "trained" on my data, because it looks things up (RAG) instead.
- Sources are hidden for now, because the API returns all 5 chunks, not only the ones Claude used. They come back as "Read more" links later.
- On the bot: CORS middleware lets only my website, its Vercel previews and local development call the API from a browser. 21 tests.

**My answer (1):** CORS is a browser safety rule: a web page may only call APIs at its own address unless the API says the page is allowed. My website and my bot run at different addresses, so the bot's CORS middleware allows only my site (plus its previews and local development). Other sites can't use my bot from a browser. My Express backend's `cors` package does the same job for my articles.

**My answer (2):** `src/layout/Main.jsx` wraps every page and stays on screen while I navigate. If the bubble and the chat page each kept their own state, the conversation would be lost when switching between them. So the conversation lives in a Provider (React Context) in the layout, "lifting state up", and both read the same conversation.

## Day 11 (Nov 9): My detailed profile, by interview
- The bot's answers can only be as good as its data, and my resume was too short and formal. So Claude interviewed me in 4 batches (my story, my work in depth, skills and how I work, goals and fun) and wrote `data/profile/about-me.md` in my voice. I approved every section.
- The profile has one topic per heading, phrased like a visitor's question ("Have I held leadership roles?", "Why should you hire me?", "Do I need visa sponsorship?"), so search finds exactly the right section.
- It includes my story, both OATI roles, teamwork, leadership (president of the Mankato Cricket Club and Badminton Club MNSU), years of experience per skill, strengths, my real weakness, where I do my best work, why AI and Python, nutrition coaching, chess and cricket, and answers for salary, relocation and sponsorship.
- Privacy: the bot's copy of my resume has no dates for past jobs (`remove_past_dates()` in `resume.py`), and the bot never says when a job ended.
- Experience: the bot says "7+ years building software, counting my studies and personal projects", and only mentions how long I worked at a company when someone asks about it.
- The bot's instructions: it's "Anamul AI", it can do friendly small talk (and "hi" works now), facts about me come only from my data, articles are past writing, and when it doesn't know something it suggests a coffee chat.
- Before and after: "Are you a good leader?", "What's your biggest weakness?", "Why should we hire you?" and "hi" all went from wrong or missing to good answers.
- Mistakes I caught: a code comment and a test used my real job dates as examples, and a new test called the real Claude because it didn't use the fake. Fixed all three.

**My answer (1):** A resume doesn't have the answers to most of what people ask, and its wording is formal and generic. My detailed profile covers my story, leadership, strengths, weakness, goals and fun facts in my own words, one topic per section. Search finds exactly the right section, and the answers sound like me.

**My answer (2):** The bot finds answers in its data, so it can only say what's there. A rule like "don't mention it" is a request that could slip, but if the end date isn't in the data, the bot can't reveal it at all, like my phone number. We use both, the removed data and the rule: defense in depth.

## Day 12 (Nov 9): Live on AWS
- A question limit per visitor: 20 questions per hour per IP address. Question 21 gets a 429 ("You've asked a lot of questions!") and never reaches Claude, so nobody can run up my bill. Counted per running server, which is enough for the beta. 25 tests.
- Docker: the `Dockerfile` starts from AWS's Lambda Python 3.13 image, installs only the packages the bot needs (from `uv.lock`, no pytest), and copies in my code, chunks and embeddings. `.dockerignore` keeps `.env` out, and I checked that the image has no `.env` inside.
- Mangum connects AWS Lambda to FastAPI (`lambda_handler.py`). I tested the image locally the way Lambda runs it before deploying.
- On AWS (us-east-2): an ECR repository for the image, an IAM role that only lets Lambda run and write logs, the Lambda function (arm64, 1 GB, 60-second timeout), and a public Function URL.
- My keys: `scripts/set_lambda_keys.sh` copies them from `.env` into Lambda's settings (encrypted by AWS) and never prints them.
- `scripts/deploy.sh` rebuilds the image, pushes it, and updates Lambda with one command.
- First live answer from AWS: "Tell me about yourself" in about 6.6 seconds, including the cold start.
- I added a payment method on Voyage (my billing details first), so the live bot isn't stuck at 3 questions a minute. The free tokens still apply.
- Small lessons: in zsh, `$REPO:latest` is read as a special modifier, so write `${REPO}:latest`. A brand-new IAM role takes a few seconds before Lambda can use it.

**My answer (1):** A Docker image is a sealed box with everything my bot needs to run: Python, its packages, my code, and my chunks and embeddings. It runs the same on AWS as on my laptop, so there are no "it works on my machine" surprises. AWS Lambda runs my bot straight from that image.

**My answer (2):** The image gets copied to ECR, and anyone with a copy could open it, so secrets must never be inside it (`.dockerignore` keeps `.env` out). My keys live in Lambda's settings instead: encrypted by AWS, separate from the code, and easy to change without rebuilding, like Vercel's environment variables for my website.

## Day 13 (Nov 10): The beta is live on anamulhasan.com
- My website now talks to the bot on AWS. In Vercel I added `VITE_ANAMUL_AI_URL` (the Lambda Function URL) for Production and Preview, as a **Config** value, not a Secret: Vite copies every `VITE_` variable into the website's JavaScript when it builds, so anyone can read it in their browser. Fine for a public URL, never for a key.
- Because the value is copied in at build time, the old preview didn't change until Vercel built it again. A new commit did that.
- The website drops a trailing slash from the URL, so a request can never go to `//ask`.
- CORS from Day 10 already allowed my preview links, so the preview worked against AWS on the first try.
- Tested the preview on my laptop, and at phone size (375 px): the floating bubble, the /chat page and dark mode. With the bot warm, an answer took about 2.3 seconds.
- Bug found in testing: in dark mode the chat box had a lighter rectangle inside it. My site's global dark style for all text boxes was more specific in CSS than `dark:bg-transparent`, so it won. Tailwind's `!bg-transparent` (important) fixed it.
- I said "merge it", main was fast-forwarded to the branch, Vercel built production in about a minute, and Anamul AI answered "Which book changed your life?" on anamulhasan.com.
- AWS housekeeping the same night: confirmed my account and root email, MFA on both root and my IAM user, no root access keys, and the bill so far is $0.00.

**My answer (1):** When Vercel builds my website, it bakes every `VITE_` variable into the finished files, like ingredients in a cake. The old preview was baked before I added the bot's address, so it needed a new build. And since every visitor gets those files, anyone can read a `VITE_` variable. That's fine for a public address, but my API keys stay hidden in Lambda.

**My answer (2):** My website runs in the visitor's browser, and their question goes straight to my bot on AWS Lambda, not through Vercel. After the CORS check, the bot finds the 5 pieces of my data closest in meaning to the question (with Voyage), and Claude writes the answer in my voice from them. The answer comes back to the chat in about 2 seconds.

## Day 14 (Nov 11): Better answers from real use
- The first real "hi" on the live site got a list of topics and hobbies. Search still hands Claude the 5 closest chunks, even for a greeting, and "two to four sentences" invited it to fill the space. New rule: hi, thanks and bye get one short sentence.
- I asked the live bot 10 common visitor questions. The facts were right, but four patterns made the answers heavy: hobbies in almost every answer, a long "Who are you?" that switched voices, too many coffee-chat links, and five-sentence answers. Four new rules fixed them: hobbies only when asked; a one-or-two-sentence "Who are you?"; the coffee chat only when the bot can't answer, or for salary, goals or meeting the real me; two or three sentences.
- I tested the same questions before and after, locally first, then deployed. "What do you do for fun?" still talks about cricket and chess, because that's what was asked.
- The data mattered as much as the instructions. "Chess with chai" came from my About page, and with no favorite book in my profile, the bot hedged and pushed a coffee chat. I rewrote my About page's quick facts as 9 specific cards (preview branch, then "merge it"), gave the bot the same facts, and added my favorite book, *Atomic Habits*, the book that changed my life.
- Any data change means: update `data/profile`, re-chunk (now 119 chunks), re-embed (17,698 Voyage tokens), and deploy.

**My answer (1):** Even for "hi", the bot searched my data and gave Claude the 5 closest chunks, and my instructions asked for two to four sentences, so Claude filled the space with facts about me. A new rule fixed it: hi, thanks and bye get one short sentence, with no facts nobody asked for.

**My answer (2):** The bot can only be as good as what I give it. "Chess with chai" came straight from my About page, and with no favorite book in my profile, it could only hedge and suggest a coffee chat. The instructions control how it answers, but the data decides what it can say.
