"""Tests for the similarity math in embed.py."""

import pytest

from anamul_ai.embed import similarity


def test_same_direction_is_a_perfect_match():
    # [2, 4, 6] points the same way as [1, 2, 3], just twice as long
    assert similarity([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)  # approx: floating-point math is off by a hair


def test_unrelated_is_zero():
    assert similarity([1, 0], [0, 1]) == 0  # At a right angle: nothing in common


def test_opposite_is_minus_one():
    assert similarity([1, 0], [-1, 0]) == -1
