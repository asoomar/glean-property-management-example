"""Validate chatbot answers against facts from the Northstar policy documents.

Runs live Search + Chat calls. Requires .env tokens and indexed documents.

Usage:
    python validate.py
"""

from __future__ import annotations

import re
import sys

from chat import ask

# Each case checks that Glean returns an answer mentioning facts from the docs.
# answer_contains_any: at least one phrase must appear (case-insensitive)
# source_titles_any: optional — at least one expected source title (partial match)
CASES = [
    {
        "question": "What is the initial late fee?",
        "answer_contains_any": ["$95", "95"],
        "source_titles_any": ["Standard Lease Terms", "Rent Payments"],
    },
    {
        "question": "What is the monthly pet rent?",
        "answer_contains_any": ["$35", "35"],
        "source_titles_any": ["Pet", "Animal"],
    },
    {
        "question": "What is the short-term premium for a 6-month lease?",
        "answer_contains_any": ["$150", "150"],
        "source_titles_any": ["Standard Lease Terms"],
    },
    {
        "question": "What is the target response time for an emergency maintenance request?",
        "answer_contains_any": ["immediate", "immediate dispatch"],
        "source_titles_any": ["Maintenance"],
    },
    {
        "question": "What is the month-to-month rent premium after lease expiration?",
        "answer_contains_any": ["$300", "300"],
        "source_titles_any": ["Standard Lease Terms"],
    },
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower()


def _check_case(case: dict) -> tuple[bool, str]:
    response = ask(case["question"])
    answer = _normalize(response.get("answer") or "")
    sources = response.get("sources") or []

    if not answer:
        return False, "empty answer"

    expected = case["answer_contains_any"]
    if not any(_normalize(term) in answer for term in expected):
        return False, f"answer missing any of {expected!r}"

    expected_sources = case.get("source_titles_any")
    if expected_sources:
        titles = " ".join(source.get("title") or "" for source in sources).lower()
        if not any(term.lower() in titles for term in expected_sources):
            return False, f"sources missing any of {expected_sources!r}"

    return True, "ok"


def main() -> int:
    print(f"Running {len(CASES)} validation case(s)...\n")
    failures = 0

    for i, case in enumerate(CASES, 1):
        question = case["question"]
        try:
            passed, detail = _check_case(case)
        except Exception as exc:
            passed, detail = False, str(exc)

        status = "PASS" if passed else "FAIL"
        print(f"{status} [{i}/{len(CASES)}] {question}")
        if not passed:
            failures += 1
            print(f"       {detail}")

    print()
    if failures:
        print(f"{failures} case(s) failed.")
        return 1

    print("All validation cases passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
