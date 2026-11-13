"""Tests for the eval checker. They check made-up answers, so they never call Claude."""

import json

from anamul_ai.evals import CASES_FILE, check, count_sentences


def test_a_good_answer_passes():
    case = {"include": ["Atomic Habits"], "exclude": ["chai"], "max_sentences": 2}
    assert check("My favorite book is Atomic Habits.", case) == []


def test_a_missing_fact_is_a_problem():
    assert check("I like reading.", {"include": ["Atomic Habits"]}) == ['should say "Atomic Habits"']


def test_one_of_several_wordings_is_enough():
    case = {"include_any": ["AI avatar", "AI version"]}
    assert check("I'm an AI version of Anamul.", case) == []
    assert len(check("I'm Anamul.", case)) == 1


def test_a_forbidden_word_is_a_problem_in_any_letter_case():
    assert check("I love Chess with CHAI.", {"exclude": ["chai"]}) == ['should not say "chai"']


def test_a_forbidden_pattern_catches_any_year():
    case = {"exclude_pattern": r"\b(19|20)\d{2}\b"}
    assert check("I'm no longer there and open to new roles.", case) == []
    assert len(check("I worked there until 1999.", case)) == 1


def test_sentences_are_counted_without_tripping_on_web_addresses():
    assert count_sentences("Hi! I'm Anamul's AI avatar. What would you like to know?") == 3
    assert count_sentences("I play on chess.com and write at anamulhasan.com every week.") == 1


def test_a_long_answer_is_a_problem():
    problems = check("One. Two. Three.", {"max_sentences": 2})
    assert problems == ["too long: 3 sentences, the limit is 2"]


def test_every_case_has_a_question_and_at_least_one_rule():
    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    rules = {"include", "include_any", "exclude", "exclude_pattern", "max_sentences"}
    assert len({case["id"] for case in cases}) == len(cases)  # No duplicate ids
    for case in cases:
        assert case["question"] and rules & set(case), case["id"]
