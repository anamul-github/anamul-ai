#!/usr/bin/env bash
# Copy my API keys from .env into the Lambda function's settings, without printing them.
# Run from the repo root: ./scripts/set_lambda_keys.sh
set -euo pipefail

set -a; source .env; set +a  # Loads ANTHROPIC_API_KEY and VOYAGE_API_KEY
: "${ANTHROPIC_API_KEY:?ANTHROPIC_API_KEY is missing from .env}"
: "${VOYAGE_API_KEY:?VOYAGE_API_KEY is missing from .env}"

aws lambda update-function-configuration --function-name anamul-ai --region us-east-2 \
  --environment "Variables={ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY},VOYAGE_API_KEY=${VOYAGE_API_KEY}}" \
  --query 'LastUpdateStatus' --output text >/dev/null  # Never print the response: it contains the keys
aws lambda wait function-updated-v2 --function-name anamul-ai --region us-east-2
echo "Done: both keys are saved in Lambda (encrypted by AWS, not printed anywhere)."
