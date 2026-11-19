# The bot as an AWS Lambda container image.
# AWS's Lambda Web Adapter runs it as a normal web server (uvicorn) inside Lambda. That's what lets an
# answer stream to the visitor word by word; the old Mangum handler could only send it all at the end.
# Built on AWS's own Lambda Python image: Lambda keeps its layers cached, so cold starts load much faster
# than a generic Python image (that one went past Lambda's 10-second startup limit).
# Build: docker build --platform linux/arm64 -t anamul-ai .
FROM public.ecr.aws/lambda/python:3.13

COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:1.1.0 /lambda-adapter /opt/extensions/lambda-adapter
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /bin/uv
WORKDIR ${LAMBDA_TASK_ROOT}

# Only the packages the bot needs to run (no pytest), at the exact versions in uv.lock, already compiled
COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-dev --no-emit-project --no-hashes -o requirements.txt \
    && uv pip install --system --no-cache --compile-bytecode -r requirements.txt

COPY src/anamul_ai ./anamul_ai
# Compile to bytecode now: Lambda's disk is read-only, so otherwise every cold start compiles everything again
RUN python -m compileall -q anamul_ai
# The chunks and embeddings are built on my laptop; my keys come from Lambda's settings, never from a file
COPY data/chunks.jsonl data/embeddings.json ./data/

# Stream responses instead of buffering them. Async init: if startup is slow, let the adapter finish it
# during the first request instead of hitting Lambda's 10-second limit and starting over.
ENV AWS_LWA_INVOKE_MODE=response_stream AWS_LWA_ASYNC_INIT=true PORT=8080
# Run the web server directly, instead of the base image's usual Lambda handler
ENTRYPOINT ["python", "-m", "uvicorn", "anamul_ai.api:app", "--host", "0.0.0.0", "--port", "8080"]
