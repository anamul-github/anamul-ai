"""Scores the bot on a fixed set of questions, so I can tell whether a change made it better or worse.

Run: uv run python -m anamul_ai.evals (asks the real Claude and Voyage, about 1-2 cents per question)
"""

import json
import re
from pathlib import Path

from anamul_ai.answer import write_answer
from anamul_ai.api import find_chunks

CASES_FILE = Path("evals/cases.json")
RESULTS_FILE = Path("evals/last_run.json")  # Every answer from the last run, to read the failures; not committed
# The end of a sentence: punctuation, then a space, then a capital letter (so "chess.com" isn't an ending)
SENTENCE_END = re.compile(r"[.!?]+[\"')*]*\s+(?=[A-Z\"*(])")


def count_sentences(text: str) -> int:
    return len(SENTENCE_END.findall(text.strip())) + 1


def check(answer: str, case: dict) -> list[str]:
    """Every rule of the case that this answer breaks. An empty list means it passed."""
    problems = []
    lower = answer.lower()
    for text in case.get("include", []):
        if text.lower() not in lower:
            problems.append(f'should say "{text}"')
    any_of = case.get("include_any", [])
    if any_of and not any(text.lower() in lower for text in any_of):
        problems.append(f"should say one of: {', '.join(any_of)}")
    for text in case.get("exclude", []):
        if text.lower() in lower:
            problems.append(f'should not say "{text}"')
    pattern = case.get("exclude_pattern")
    if pattern and re.search(pattern, answer):
        problems.append(f"matches the forbidden pattern {pattern}")
    limit = case.get("max_sentences")
    if limit and count_sentences(answer) > limit:
        problems.append(f"too long: {count_sentences(answer)} sentences, the limit is {limit}")
    return problems


def ask_bot(question: str) -> str:
    """The same two steps as /ask: find the closest chunks, then let Claude answer from them."""
    results = find_chunks(question)
    return write_answer(question, [result.chunk.text for result in results])


def main() -> None:
    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    results = []
    for case in cases:
        answer = ask_bot(case["question"])
        problems = check(answer, case)
        results.append({**case, "answer": answer, "problems": problems})
        print(f"{'✅' if not problems else '❌'} {case['id']}: {case['question']}")
        for problem in problems:
            print(f"     {problem}")
        if problems:
            print(f"     Answer: {answer}")

    passed = sum(1 for result in results if not result["problems"])
    print(f"\nScore: {passed}/{len(results)} ({passed / len(results):.0%})")
    RESULTS_FILE.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Every answer is saved in {RESULTS_FILE}")


if __name__ == "__main__":
    main()
