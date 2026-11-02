import unittest

from src.quiz_validation import validate_quiz_payload


def valid_quiz(count=3):
    return {
        "title": "Operating Systems Quiz",
        "questions": [
            {
                "question": f"Question {index}?",
                "options": ["A", "B", "C", "D"],
                "correct_index": 1,
                "explanation": "B is correct because it matches the concept.",
            }
            for index in range(count)
        ],
    }


class QuizValidationTests(unittest.TestCase):
    def test_accepts_and_normalizes_valid_quiz(self):
        quiz = valid_quiz()
        quiz["title"] = "  Operating Systems Quiz  "
        quiz["questions"][0]["question"] = "  Question 1?  "
        result = validate_quiz_payload(quiz, 3)
        self.assertEqual(result["title"], "Operating Systems Quiz")
        self.assertEqual(result["questions"][0]["question"], "Question 1?")
        self.assertEqual(len(result["questions"]), 3)

    def test_rejects_non_object_payload(self):
        with self.assertRaisesRegex(ValueError, "JSON object"):
            validate_quiz_payload([], 3)

    def test_requires_exact_requested_question_count(self):
        with self.assertRaisesRegex(ValueError, "exactly 3"):
            validate_quiz_payload(valid_quiz(2), 3)

    def test_rejects_invalid_expected_count(self):
        for count in (True, 2, 11, 3.0):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    validate_quiz_payload(valid_quiz(), count)

    def test_rejects_missing_title(self):
        quiz = valid_quiz()
        quiz["title"] = " "
        with self.assertRaisesRegex(ValueError, "non-empty title"):
            validate_quiz_payload(quiz, 3)

    def test_rejects_non_object_question(self):
        quiz = valid_quiz()
        quiz["questions"][1] = "not an object"
        with self.assertRaisesRegex(ValueError, "Question 2"):
            validate_quiz_payload(quiz, 3)

    def test_requires_four_non_empty_options(self):
        quiz = valid_quiz()
        quiz["questions"][0]["options"] = ["A", "B", "C"]
        with self.assertRaisesRegex(ValueError, "exactly four"):
            validate_quiz_payload(quiz, 3)

    def test_rejects_duplicate_options(self):
        quiz = valid_quiz()
        quiz["questions"][0]["options"] = ["A", "B", "a", "C"]
        with self.assertRaisesRegex(ValueError, "distinct"):
            validate_quiz_payload(quiz, 3)

    def test_rejects_invalid_correct_index_including_boolean(self):
        for value in (True, -1, 4, "1", 1.0):
            with self.subTest(value=value):
                quiz = valid_quiz()
                quiz["questions"][0]["correct_index"] = value
                with self.assertRaisesRegex(ValueError, "correct_index"):
                    validate_quiz_payload(quiz, 3)

    def test_requires_non_empty_explanation(self):
        quiz = valid_quiz()
        quiz["questions"][0]["explanation"] = ""
        with self.assertRaisesRegex(ValueError, "explanation"):
            validate_quiz_payload(quiz, 3)

    def test_drops_unrecognized_model_fields(self):
        quiz = valid_quiz()
        quiz["debug"] = "unexpected"
        quiz["questions"][0]["provider_metadata"] = {"secret": "unused"}
        result = validate_quiz_payload(quiz, 3)
        self.assertNotIn("debug", result)
        self.assertNotIn("provider_metadata", result["questions"][0])


if __name__ == "__main__":
    unittest.main()
