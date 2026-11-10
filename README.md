# Anamul AI

A chatbot that answers questions about Anamul Hasan (resume, projects, articles and book notes), with sources.
Built in 30 days, November 2026: Python, FastAPI, Claude API, PostgreSQL + pgvector, LangGraph, AWS.

**Try it (beta):** [anamulhasan.com/chat](https://www.anamulhasan.com/chat)

## How it works
1. **Collect:** my articles, book notes, resume, About page and projects are saved as Markdown in `data/`.
2. **Chunk:** everything is split into small sections, each labeled with where it came from (like *Resume > Work experience > DevOps Engineer*).
3. **Search:** find the chunks closest in meaning to the question, using embeddings (meaning fingerprints) from Voyage AI. They're in a local file for now; PostgreSQL + pgvector is next.
4. **Answer:** Claude (Opus 5.5) writes a short answer from those chunks, speaking as me, and returns its sources.
5. **Ship:** the API runs on AWS Lambda from a Docker image, with a limit of 20 questions per hour per visitor. Visitors chat with it as "Anamul AI" on [anamulhasan.com](https://www.anamulhasan.com/chat), on a chat page or from a floating chat bubble.

## Progress
- [x] Day 1: set up Python with uv, and learn Python basics as a JavaScript developer
- [x] Day 2: download my articles and book notes from anamulhasan.com
- [x] Day 3: add my resume, About page and projects, then split everything into 87 searchable chunks
- [x] Day 4: my first API with FastAPI, with a keyword search that showed why the bot needs to search by meaning
- [x] Day 5: 8 automated tests with pytest for the chunker and the API
- [x] Day 6: `POST /ask`, the endpoint the chat widget will call, which returns an answer with its sources (12 tests)
- [x] Day 7: my first message to Claude through the API, with the key kept safely in `.env`
- [x] Day 8: Claude writes the answers in `/ask`, in my voice, using only the matching chunks (14 tests)
- [x] Day 9: search by meaning with Voyage AI embeddings, so "Tell me about yourself?" now finds my About page (19 tests)
- [x] Day 10: "Anamul AI" on my website: a chat page and a floating bubble, talking to this API (CORS, 21 tests)
- [x] Day 11: a detailed profile in my own words, written from an interview, so the bot knows me much better (24 tests)
- [x] Day 12: live on AWS Lambda from a Docker image, with a question limit per visitor and my keys kept out of the image (25 tests)
- [x] Day 13: the beta is live: my website talks to the bot on AWS, so anyone can chat with it at [anamulhasan.com/chat](https://www.anamulhasan.com/chat)
- [ ] Nov 15–21: learn from real questions (logs and feedback), an eval score, pgvector, Terraform, GitHub Actions
- [ ] Nov 22–30: follow-up questions, a LangGraph agent, streaming answers, and v1.0

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
uv run python -m anamul_ai.embed        # Day 9: meaning fingerprints for every chunk (needs VOYAGE_API_KEY in .env)
./scripts/deploy.sh                     # Day 12: build the Docker image, push it to ECR, update the Lambda function
./scripts/set_lambda_keys.sh            # Day 12: copy the API keys from .env into Lambda (prints nothing secret)
```
