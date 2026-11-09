# Anamul AI

A chatbot that answers questions about Anamul Hasan (resume, projects, articles and book notes), with sources.
Built in 30 days, November 2026: Python, FastAPI, Claude API, PostgreSQL + pgvector, LangGraph, AWS.

## How it works
1. **Collect:** my articles, book notes, resume, About page and projects are saved as Markdown in `data/`.
2. **Chunk:** everything is split into small sections, each labeled with where it came from (like *Resume > Work experience > DevOps Engineer*).
3. **Search** *(coming in Week 2)*: find the chunks that match a question by meaning, using embeddings in PostgreSQL + pgvector.
4. **Answer** *(coming in Week 2)*: Claude writes the answer from those chunks and cites its sources.
5. **Ship** *(coming in Weeks 3–4)*: an API on AWS and a chat widget on [anamulhasan.com](https://www.anamulhasan.com).

## Progress
- [x] Day 1: set up Python with uv, and learn Python basics as a JavaScript developer
- [x] Day 2: download my articles and book notes from anamulhasan.com
- [x] Day 3: add my resume, About page and projects, then split everything into 87 searchable chunks
- [x] Day 4: my first API with FastAPI, with a keyword search that showed why the bot needs to search by meaning
- [x] Day 5: 8 automated tests with pytest for the chunker and the API
- [x] Day 6: `POST /ask`, the endpoint the chat widget will call, which returns an answer with its sources (12 tests)
- [x] Day 7: my first message to Claude through the API, with the key kept safely in `.env`
- [ ] Week 2: Claude API, search with pgvector, and a set of test questions
- [ ] Week 3: Docker, then AWS with Terraform and GitHub Actions
- [ ] Week 4: chat widget on anamulhasan.com, a LangGraph agent, and launch

What I learned each day is in [LEARNING.md](LEARNING.md).

## Run
```
uv run python learn/day01_about_me.py   # Day 1: Python basics
uv run python -m anamul_ai.collect      # Day 2: download articles and book notes into data/
uv run python -m anamul_ai.resume ~/Desktop/Anamul-Hasan-Resume.pdf   # Day 3: resume PDF to data/profile/resume.md (phone removed)
uv run python -m anamul_ai.chunk        # Day 3: split data/ into searchable chunks (data/chunks.jsonl)
uv run fastapi dev src/anamul_ai/api.py # Day 4: the API; try it at http://127.0.0.1:8000/docs
uv run pytest                           # Day 5: run the tests in tests/
cp .env.example .env                    # Day 7: once, then put your Claude API key in .env (never commit it)
uv run python learn/day07_hello_claude.py   # Day 7: first message to Claude
```
