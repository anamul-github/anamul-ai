#!/usr/bin/env bash
# Build the bot's image, push it to ECR, and point the Lambda function at it.
# Run from the repo root after changing code or data: ./scripts/deploy.sh
set -euo pipefail

REGION=us-east-2
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGISTRY="${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com"
IMAGE="${REGISTRY}/anamul-ai:latest"

aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$REGISTRY" >/dev/null
docker buildx build --platform linux/arm64 --provenance=false -t "$IMAGE" --push .
aws lambda update-function-code --function-name anamul-ai --region "$REGION" --image-uri "$IMAGE" \
  --query 'LastUpdateStatus' --output text >/dev/null  # Never print the response: it lists the function's settings
aws lambda wait function-updated-v2 --function-name anamul-ai --region "$REGION"
echo "Deployed: Lambda is running the new image."
