# Day 7: my first message to Claude.
# Sends one short question, then prints the answer, the tokens it used and what it cost.
# Run it with:  uv run python learn/day07_hello_claude.py

import anthropic
from pydantic import ValidationError

from anamul_ai.config import Settings

MODEL = "claude-opus-5-5"
# Claude Opus 5.5 prices in dollars per million tokens (November 2026)
INPUT_PRICE = 4.00
OUTPUT_PRICE = 20.00

try:
    settings = Settings()  # Reads ANTHROPIC_API_KEY from .env
except ValidationError:
    raise SystemExit("ANTHROPIC_API_KEY is missing. Copy .env.example to .env and paste your key there.")

# .get_secret_value() unwraps the hidden key, only at the moment it's needed
client = anthropic.Anthropic(api_key=settings.anthropic_api_key.get_secret_value())

try:
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=1000,  # The most tokens Claude may write back; plenty for a short answer
        output_config={"effort": "low"},  # A simple question doesn't need deep thinking, which keeps it cheap
        # If Claude's safety checks ever decline a request, the API retries it on another model by itself
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=[
            {"role": "user", "content": "Hi Claude! In two sentences: what is RAG, and why does a chatbot about a person need it?"},
        ],
    )
except anthropic.AuthenticationError:
    raise SystemExit("The API key in .env was rejected. Check that you copied all of it.")

if response.stop_reason == "refusal":
    raise SystemExit("Claude declined to answer this one.")

# The response is a list of blocks (thinking, text, ...). The answer is in the "text" blocks.
for block in response.content:
    if block.type == "text":
        print(block.text)

# Tokens are the pieces of text Claude reads and writes; a token is about 3/4 of a word.
usage = response.usage
cost = usage.input_tokens / 1_000_000 * INPUT_PRICE + usage.output_tokens / 1_000_000 * OUTPUT_PRICE
print(f"\nModel: {response.model}")
print(f"Tokens: {usage.input_tokens} in, {usage.output_tokens} out")
print(f"Cost: ${cost:.5f}")
