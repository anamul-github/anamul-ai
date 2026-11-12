"""Tests for saving chats. A fake table stands in for DynamoDB, so nothing touches AWS."""

import time

import pytest

from anamul_ai import chats


class FakeTable:
    def __init__(self):
        self.items = []

    def put_item(self, Item):
        self.items.append(Item)


@pytest.fixture
def fake_table(monkeypatch):
    table = FakeTable()
    monkeypatch.setattr(chats, "get_table", lambda: table)
    return table


def test_nothing_is_saved_outside_aws_lambda(monkeypatch, fake_table):
    monkeypatch.delenv("AWS_LAMBDA_FUNCTION_NAME", raising=False)
    assert chats.save_chat("hi", "Hi!", []) is None
    assert fake_table.items == []


def test_a_chat_is_saved_on_lambda_with_no_personal_details(monkeypatch, fake_table):
    monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "anamul-ai")
    chat_id = chats.save_chat("Which book changed your life?", "Atomic Habits.", ["Profile"])
    item = fake_table.items[0]
    assert item["id"] == chat_id and len(chat_id) == 32
    assert set(item) == {"id", "created_at", "question", "answer", "sources", "expires_at"}  # No IP address
    days_kept = (item["expires_at"] - time.time()) / 86400
    assert 89 < days_kept <= 90


def test_a_failed_save_does_not_break_the_answer(monkeypatch):
    class BrokenTable:
        def put_item(self, Item):
            raise RuntimeError("DynamoDB is down")

    monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "anamul-ai")
    monkeypatch.setattr(chats, "get_table", lambda: BrokenTable())
    assert chats.save_chat("hi", "Hi!", []) is None
