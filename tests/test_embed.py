"""Day 9: tests for the similarity math in embed.py. Run them with:  uv run pytest"""

import pytest

from anamul_ai.embed import similarity


def test_same_direction_is_a_perfect_match():
    # [2, 4, 6] is [1, 2, 3] made twice as long: it points the same way, so it means the same
    assert similarity([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)  # approx: decimals can be off by a tiny bit


def test_unrelated_is_zero():
    assert similarity([1, 0], [0, 1]) == 0  # At a right angle: nothing in common


def test_opposite_is_minus_one():
    assert similarity([1, 0], [-1, 0]) == -1
