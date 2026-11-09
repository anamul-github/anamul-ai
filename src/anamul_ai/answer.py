"""Claude writes the answer to a question, using only the chunks that search found."""

from functools import cache

import anthropic

from anamul_ai.config import get_settings

SYSTEM_PROMPT = """You are "Ask Anamul", the chatbot on Anamul Hasan's website, anamulhasan.com. \
Recruiters and visitors ask about Anamul's work, skills, projects, writing and life.

Speak as Anamul, in the first person ("At OATI, I led..."), in a friendly, humble and plain way. \
Keep answers short: two to four sentences. Never exaggerate; stay close to what the sources say.

Use only the sources in the user's message. Never add facts from anywhere else. \
If the sources don't answer the question, say you don't know that yet and suggest reaching out \
through anamulhasan.com.

If someone asks whether they're talking to the real Anamul, say you're an AI assistant that \
answers from his resume, projects and writing."""


@cache  # One client, created the first time an answer is needed
def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=get_settings().anthropic_api_key.get_secret_value())


def write_answer(question: str, sources: list[str]) -> str:
    """Ask Claude to answer the question from these chunk texts only."""
    # Numbered <source> tags help Claude tell the chunks apart
    source_blocks = "\n\n".join(
        f'<source id="{number}">\n{text}\n</source>' for number, text in enumerate(sources, start=1)
    )
    response = get_client().beta.messages.create(
        model=get_settings().claude_model,
        max_tokens=2000,  # Room for brief thinking plus a two-to-four sentence answer
        output_config={"effort": "low"},  # Answering from given sources is simple, so keep it fast and cheap
        # If a safety check declines, the API retries on another model (Opus 5.5 only; remove for Haiku)
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"<sources>\n{source_blocks}\n</sources>\n\nQuestion: {question}"}],
    )
    if response.stop_reason == "refusal":
        return "Sorry, I can't help with that one."
    return "".join(block.text for block in response.content if block.type == "text").strip()
