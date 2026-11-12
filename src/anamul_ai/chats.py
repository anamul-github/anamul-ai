"""Saves each chat in DynamoDB, so I can see what visitors ask and which answers they liked.

Read the latest chats: uv run python -m anamul_ai.chats (or add a number, like 50)
"""

import os
import sys
import time
import uuid
from datetime import datetime, timezone
from functools import cache

import boto3
from botocore.exceptions import ClientError

TABLE_NAME = "anamul-ai-chats"
KEEP_DAYS = 90  # DynamoDB deletes a chat by itself once expires_at has passed


def saving_enabled() -> bool:
    # Only the live bot on AWS Lambda saves chats, so my local runs and tests never fill the table
    return "AWS_LAMBDA_FUNCTION_NAME" in os.environ


@cache
def get_table():
    return boto3.resource("dynamodb", region_name="us-east-2").Table(TABLE_NAME)


def save_chat(question: str, answer: str, sources: list[str]) -> str | None:
    """Save one question and answer, with no IP address or name. Returns the chat's id, or None if not saved."""
    if not saving_enabled():
        return None
    chat_id = uuid.uuid4().hex
    try:
        get_table().put_item(Item={
            "id": chat_id,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "question": question,
            "answer": answer,
            "sources": sources,
            "expires_at": int(time.time()) + KEEP_DAYS * 86400,
        })
    except Exception as error:  # A failed save must never cost the visitor their answer
        print(f"Could not save chat: {error}")
        return None
    return chat_id


def save_feedback(chat_id: str, rating: str) -> bool:
    """Record a thumbs up ("up") or down ("down") on a saved chat. False if there's no such chat."""
    if not saving_enabled():
        return False
    try:
        get_table().update_item(
            Key={"id": chat_id},
            UpdateExpression="SET rating = :rating",
            ConditionExpression="attribute_exists(id)",  # Only rate real chats; never create new rows
            ExpressionAttributeValues={":rating": rating},
        )
    except ClientError as error:
        if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise
    return True


def recent_chats() -> list[dict]:
    """Every saved chat, newest first. Reading uses my own AWS login; the live bot can only write."""
    table, items, page_args = get_table(), [], {}
    while True:
        page = table.scan(**page_args)
        items += page["Items"]
        if "LastEvaluatedKey" not in page:
            break
        page_args["ExclusiveStartKey"] = page["LastEvaluatedKey"]
    return sorted(items, key=lambda item: item["created_at"], reverse=True)


def main() -> None:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    chats = recent_chats()
    ratings = [chat.get("rating") for chat in chats]
    print(f"{len(chats)} chats saved · 👍 {ratings.count('up')} · 👎 {ratings.count('down')} · newest {limit} below\n")
    for chat in chats[:limit]:
        when = datetime.fromisoformat(chat["created_at"]).astimezone().strftime("%b %-d, %-I:%M %p")
        rating = {"up": "👍", "down": "👎"}.get(chat.get("rating"), "")
        print(f"{when}  {rating}\nQ: {chat['question']}\nA: {chat['answer']}\n")


if __name__ == "__main__":
    main()
