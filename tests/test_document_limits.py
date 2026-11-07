import unittest

from src.services.document_limits import (
    MAX_DOCUMENT_CHARS,
    MAX_UPLOAD_BYTES,
    validate_extracted_text,
    validate_upload_size,
)


class DocumentLimitsTests(unittest.TestCase):
    def test_accepts_upload_within_size_limit(self):
        validate_upload_size(1)
        validate_upload_size(MAX_UPLOAD_BYTES)

    def test_rejects_empty_or_invalid_upload_size(self):
        for size in (0, -1, True, 1.5):
            with self.subTest(size=size):
                with self.assertRaises(ValueError):
                    validate_upload_size(size)

    def test_rejects_upload_above_size_limit(self):
        with self.assertRaisesRegex(ValueError, "10 MB"):
            validate_upload_size(MAX_UPLOAD_BYTES + 1)

    def test_accepts_text_within_extraction_limit(self):
        text = "x" * MAX_DOCUMENT_CHARS
        self.assertEqual(validate_extracted_text(text), text)

    def test_rejects_extracted_text_above_limit(self):
        with self.assertRaisesRegex(ValueError, "50,000 characters"):
            validate_extracted_text("x" * (MAX_DOCUMENT_CHARS + 1))


if __name__ == "__main__":
    unittest.main()
