# The bot as an AWS Lambda container image.
# Build: docker build --platform linux/arm64 -t anamul-ai .
FROM public.ecr.aws/lambda/python:3.13

COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /bin/uv
WORKDIR ${LAMBDA_TASK_ROOT}

# Only the packages the bot needs to run (no pytest), at the exact versions in uv.lock
COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-dev --no-emit-project --no-hashes -o requirements.txt \
    && uv pip install --no-cache --target . -r requirements.txt

COPY src/anamul_ai ./anamul_ai
# The chunks and embeddings are built on my laptop; my keys come from Lambda's settings, never from a file
COPY data/chunks.jsonl data/embeddings.json ./data/

CMD ["anamul_ai.lambda_handler.handler"]
