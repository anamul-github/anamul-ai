# The bot as an AWS Lambda container image.
# AWS's Lambda Web Adapter runs it as a normal web server (uvicorn) inside Lambda. That's what lets an
# answer stream to the visitor word by word; the old Mangum handler could only send it all at the end.
# Build: docker build --platform linux/arm64 -t anamul-ai .
FROM public.ecr.aws/docker/library/python:3.13-slim

COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:1.1.0 /lambda-adapter /opt/extensions/lambda-adapter
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /bin/uv
WORKDIR /var/task

# Only the packages the bot needs to run (no pytest), at the exact versions in uv.lock
COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-dev --no-emit-project --no-hashes -o requirements.txt \
    && uv pip install --system --no-cache -r requirements.txt

COPY src/anamul_ai ./anamul_ai
# The chunks and embeddings are built on my laptop; my keys come from Lambda's settings, never from a file
COPY data/chunks.jsonl data/embeddings.json ./data/

# Stream responses instead of buffering them; the adapter forwards requests to port 8080
ENV AWS_LWA_INVOKE_MODE=response_stream PORT=8080
CMD ["uvicorn", "anamul_ai.api:app", "--host", "0.0.0.0", "--port", "8080"]
