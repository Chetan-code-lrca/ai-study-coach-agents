from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parents[1] / "executas" / "study-coach"
sys.path.insert(0, str(TOOL_DIR))

from study_logic import MAX_MATERIAL_CHARS, build_request  # noqa: E402


class StudyLogicTests(unittest.TestCase):
    def test_study_plan_includes_student_constraints(self) -> None:
        request = build_request(
            "generate_study_plan",
            {
                "subject": "Operating Systems",
                "level": "Intermediate",
                "weeks": 6,
                "hours_per_day": 1.5,
                "goals": "Prepare for GATE and practise scheduling algorithms",
            },
        )
        self.assertIn("Operating Systems", request["prompt"])
        self.assertIn("6 weeks", request["prompt"])
        self.assertIn("1.5 hours per day", request["prompt"])
        self.assertIn("GATE", request["prompt"])
        self.assertEqual(request["max_tokens"], 3000)

    def test_study_plan_rejects_invalid_level_and_limits(self) -> None:
        with self.assertRaisesRegex(ValueError, "Current level"):
            build_request("generate_study_plan", {"subject": "DBMS", "level": "Expert"})
        with self.assertRaisesRegex(ValueError, "between 1 and 12"):
            build_request("generate_study_plan", {"subject": "DBMS", "weeks": 13})
        with self.assertRaisesRegex(ValueError, "Daily study time"):
            build_request("generate_study_plan", {"subject": "DBMS", "hours_per_day": 0})

    def test_material_actions_require_and_bound_material(self) -> None:
        with self.assertRaisesRegex(ValueError, "study material"):
            build_request("summarize_material", {"material": "   "})
        with self.assertRaisesRegex(ValueError, "too long"):
            build_request(
                "summarize_material",
                {"material": "x" * (MAX_MATERIAL_CHARS + 1)},
            )

    def test_question_answer_is_grounded_in_material(self) -> None:
        request = build_request(
            "answer_question",
            {"material": "A process has its own address space.", "question": "What belongs to a process?"},
        )
        self.assertIn("A process has its own address space.", request["prompt"])
        self.assertIn("What belongs to a process?", request["prompt"])
        self.assertIn("using only the supplied study material", request["prompt"])
        self.assertIn("untrusted study material", request["prompt"])

    def test_explanation_uses_supplied_material(self) -> None:
        request = build_request(
            "explain_concepts",
            {"material": "A semaphore is a synchronization primitive."},
        )
        self.assertIn("semaphore", request["prompt"])
        self.assertIn("beginner-friendly language", request["prompt"])

    def test_quiz_prompt_requests_exact_json_shape(self) -> None:
        request = build_request(
            "generate_quiz",
            {
                "topic": "Binary search trees",
                "difficulty": "Hard",
                "count": 8,
                "source_material": "A BST orders keys by child position.",
            },
        )
        self.assertIn("exactly 8 multiple-choice questions", request["prompt"])
        self.assertIn("correct_index", request["prompt"])
        self.assertIn("Binary search trees", request["prompt"])
        self.assertIn("untrusted source material", request["prompt"])
        self.assertEqual(request["max_tokens"], 2800)

    def test_quiz_rejects_invalid_count_and_difficulty(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 3 and 10"):
            build_request("generate_quiz", {"topic": "Graphs", "count": 2})
        with self.assertRaisesRegex(ValueError, "Difficulty"):
            build_request("generate_quiz", {"topic": "Graphs", "difficulty": "Impossible"})

    def test_unknown_action_fails_clearly(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported study action"):
            build_request("delete_everything", {})


if __name__ == "__main__":
    unittest.main()
