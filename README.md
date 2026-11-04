# Anamul AI

A chatbot that answers questions about Anamul Hasan (resume, projects, articles and book notes), with sources.
Built in 30 days, November 2026: Python, FastAPI, Claude API, PostgreSQL + pgvector, LangGraph, AWS.

## Run
```
uv run python learn/day01_about_me.py   # Day 1: Python basics
uv run python -m anamul_ai.collect      # Day 2: download articles and book notes into data/
uv run python -m anamul_ai.resume ~/Desktop/Anamul-Hasan-Resume.pdf   # Day 3: resume PDF to data/profile/resume.md (phone removed)
uv run python -m anamul_ai.chunk        # Day 3: split data/ into searchable chunks (data/chunks.jsonl)
```
