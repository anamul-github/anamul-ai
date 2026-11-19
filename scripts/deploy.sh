#!/usr/bin/env bash
# Build the bot's image, push it to ECR, and point the Lambda function at it.
# Run from the repo root after changing code or data: ./scripts/deploy.sh
set -euo pipefail

REGION=us-east-2
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGISTRY="${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com"
REPOSITORY="${REGISTRY}/anamul-ai"
BUILD_INFO=$(mktemp)

aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$REGISTRY" >/dev/null
docker buildx build --platform linux/arm64 --provenance=false -t "${REPOSITORY}:latest" --push --metadata-file "$BUILD_INFO" .

# Deploy the exact image just built, by its digest (its fingerprint). Right after a push, the "latest" tag
# can still point at the previous image, and Lambda would then keep running the old code.
DIGEST=$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["containerimage.digest"])' "$BUILD_INFO")
aws lambda update-function-code --function-name anamul-ai --region "$REGION" --image-uri "${REPOSITORY}@${DIGEST}" \
  --query 'LastUpdateStatus' --output text >/dev/null  # Never print the response: it lists the function's settings
aws lambda wait function-updated-v2 --function-name anamul-ai --region "$REGION"

# Trust, but verify: is Lambda really running the image I just built?
RUNNING=$(aws lambda get-function --function-name anamul-ai --region "$REGION" --query 'Code.ResolvedImageUri' --output text)
if [ "$RUNNING" != "${REPOSITORY}@${DIGEST}" ]; then
  echo "NOT deployed: Lambda is running ${RUNNING##*@}, but the new image is ${DIGEST}" >&2
  exit 1
fi
echo "Deployed: Lambda is running the new image (${DIGEST:7:12})."

# The first start of a brand-new image is slow (up to ~20 s) while Lambda caches it. Pay that here with one
# request, instead of making the first visitor wait.
URL=$(aws lambda get-function-url-config --function-name anamul-ai --region "$REGION" --query FunctionUrl --output text)
SECONDS_TAKEN=$(curl -s -o /dev/null -w "%{time_total}" --max-time 60 "$URL")
echo "Warmed up: the first request took ${SECONDS_TAKEN%.*} s."
