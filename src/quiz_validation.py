"""Strict validation for model-generated multiple-choice quiz payloads."""
from __future__ import annotations

from typing import Any


def validate_quiz_payload(payload: Any, expected_count: int) -> dict[str, Any]:
    """Validate and return a minimal, normalized quiz payload.

    Reject malformed model output instead of displaying or scoring ambiguous data.
    The expected count must be the count requested by the user (3-10).
    """
    if isinstance(expected_count, bool) or not isinstance(expected_count, int):
        raise ValueError("Expected question count must be an integer.")
    if not 3 <= expected_count <= 10:
        raise ValueError("Expected question count must be between 3 and 10.")
    if not isinstance(payload, dict):
        raise ValueError("The generated quiz must be a JSON object.")

    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("The generated quiz must include a non-empty title.")

    questions = payload.get("questions")
    if not isinstance(questions, list) or len(questions) != expected_count:
        raise ValueError(f"The generated quiz must contain exactly {expected_count} questions.")

    normalized_questions: list[dict[str, Any]] = []
    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            raise ValueError(f"Question {index} must be an object.")

        prompt = question.get("question")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"Question {index} must include question text.")

        options = question.get("options")
        if not isinstance(options, list) or len(options) != 4:
            raise ValueError(f"Question {index} must have exactly four options.")
        if any(not isinstance(option, str) or not option.strip() for option in options):
            raise ValueError(f"Question {index} options must be non-empty text.")
        if len({option.strip().casefold() for option in options}) != 4:
            raise ValueError(f"Question {index} options must be distinct.")

        correct_index = question.get("correct_index")
        if isinstance(correct_index, bool) or not isinstance(correct_index, int) or not 0 <= correct_index <= 3:
            raise ValueError(f"Question {index} correct_index must be an integer from 0 to 3.")

        explanation = question.get("explanation")
        if not isinstance(explanation, str) or not explanation.strip():
            raise ValueError(f"Question {index} must include an explanation.")

        normalized_questions.append({
            "question": prompt.strip(),
            "options": [option.strip() for option in options],
            "correct_index": correct_index,
            "explanation": explanation.strip(),
        })

    return {"title": title.strip(), "questions": normalized_questions}
