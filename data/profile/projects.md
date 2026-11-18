---
title: Anamul's projects
type: projects
url: https://www.anamulhasan.com/projects
---

# Anamul's projects

## Shasongacha Foundation

Founder & Project Lead, 2025 – present. Status: building in public. Website: https://www.shasongachafoundation.org

A bilingual (Bangla/English) donation platform for my home community in Cumilla, Bangladesh.

**Why I built it:** I wanted people from Shasongacha, at home and abroad, to have a simple and transparent way to support families in need, through Zakat, Sadaqah, and community projects.

**What I built:**
- A bilingual website with a one-tap Bangla/English switch, so everyone in the community can use it.
- The foundation for online donations, with mobile and bank payments coming next.
- A plan for transparency: regular updates, reports, photos, and real stories showing how donations are used.
- I lead the vision, planning, and community side, working with my brother Mehedi Hasan, our Lead Developer.

**What I learned:** Building for your own community means trust comes first. Being open about every step matters as much as the code.

**Tech:** Next.js, React, TypeScript, Tailwind CSS, Vercel

## anamulhasan.com

Designer & Software Engineer, 2024 – present. Status: live. Website: https://www.anamulhasan.com

My website and blog, with a publishing system and serverless API I built from scratch.

**Why I built it:** I wanted one place I fully own to share what I learn, through articles and book notes, instead of spreading it across social media.

**What I built:**
- A React, Vite, and Tailwind site with a bento-style homepage and a reading layout with a progress bar and table of contents.
- A Node.js, Express, and MongoDB API running as serverless functions on Vercel, which replaced a paid always-on server.
- A private editor for articles and book notes (Firebase sign-in), with drafts and automatic rebuilds when I publish.
- Search and sharing built in: page-by-page SEO, a sitemap, and auto-generated preview cards for LinkedIn and Facebook.

**What I learned:** Owning a product end to end means caring about security, SEO, performance, and cost, not just features.

**Tech:** React, Tailwind CSS, Node.js, Express, MongoDB, Firebase, Vercel

## Anamul AI (this chatbot)

Software Engineer, 2026 – present. Status: beta. Chat: https://www.anamulhasan.com/chat. Code: https://github.com/anamul-github/anamul-ai

An AI version of me that answers questions about my work, projects, and writing, using my own words as its source.

**Why I built it:** Visitors and recruiters often have questions my pages don't answer directly. I also wanted to learn Python, applied AI, and AWS by building something real, one hour a day for 30 days.

**What I built:**
- A Python and FastAPI service that splits my resume, articles, and book notes into small sections, then finds the ones closest in meaning to each question (RAG with Voyage AI embeddings).
- Answers written by Claude in my voice, from those sections only. If my writing doesn't cover a question, it says so instead of guessing.
- A deployment on AWS Lambda from a Docker image, with a question limit per visitor and API keys kept out of the code.
- The chat page and floating chat bubble on this site, plus 25 automated tests for the service.

**What I learned:** Real questions teach more than any plan. The first live "hi" got a long list of facts nobody asked for, so now I improve the bot from how people actually use it. And it can only be as good as the writing I give it.

**Tech:** Python, FastAPI, Claude API, RAG, Voyage AI, Docker, AWS Lambda
