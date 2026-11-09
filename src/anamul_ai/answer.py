"""Day 8: Claude writes the answer from the chunks that search found.

The bot never answers from memory. Claude gets the question plus the matching
chunks, and the system prompt tells it to use only those sources.
"""

from functools import cache

import anthropic

from anamul_ai.config import get_settings

# The system prompt is Claude's standing instructions: who it is and how to answer.
SYSTEM_PROMPT = """You are "Ask Anamul", the chatbot on Anamul Hasan's website, anamulhasan.com. \
Recruiters and visitors ask about Anamul's work, skills, projects, writing and life.

Speak as Anamul, in the first person ("At OATI, I led..."), in a friendly, humble and plain way. \
Keep answers short: two to four sentences. Never exaggerate; stay close to what the sources say.

Use only the sources in the user's message. Never add facts from anywhere else. \
If the sources don't answer the question, say you don't know that yet and suggest reaching out \
through anamulhasan.com.

If someone asks whether they're talking to the real Anamul, say you're an AI assistant that \
answers from his resume, projects and writing."""


@cache  # Create the Claude client once, the first time an answer is needed
def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=get_settings().anthropic_api_key.get_secret_value())


def write_answer(question: str, sources: list[str]) -> str:
    """Ask Claude to answer the question using only these sources (chunk texts)."""
    # Wrap each chunk in <source> tags so Claude can tell them apart.
    # enumerate(..., start=1) counts 1, 2, 3..., like .map((text, i) => ...) with i + 1
    source_blocks = "\n\n".join(
        f'<source id="{number}">\n{text}\n</source>' for number, text in enumerate(sources, start=1)
    )
    response = get_client().beta.messages.create(
        model=get_settings().claude_model,
        max_tokens=2000,  # Room for Claude's brief thinking plus a two-to-four sentence answer
        output_config={"effort": "low"},  # Answering from given sources is simple, which keeps it fast and cheap
        # If a safety check declines, the API retries on another model by itself.
        # This works on Opus 5.5; remove these two lines if you switch to Haiku.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"<sources>\n{source_blocks}\n</sources>\n\nQuestion: {question}"}],
    )
    if response.stop_reason == "refusal":
        return "Sorry, I can't help with that one."
    return "".join(block.text for block in response.content if block.type == "text").strip()
