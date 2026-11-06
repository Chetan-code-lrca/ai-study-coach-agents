import pytest

from src.services.document_ingestion import (
    MAX_DOCUMENT_CHARS,
    MAX_UPLOAD_BYTES,
    extract_uploaded_text,
)


class FakeUpload:
    def __init__(self, name, data=b"", declared_size=None):
        self.name = name
        self._data = data
        self.size = len(data) if declared_size is None else declared_size
        self.read_called = False

    def getvalue(self):
        self.read_called = True
        return self._data


def test_rejects_large_declared_upload_before_reading():
    upload = FakeUpload("large.txt", declared_size=MAX_UPLOAD_BYTES + 1)

    with pytest.raises(ValueError, match="10 MiB"):
        extract_uploaded_text(upload)

    assert upload.read_called is False


def test_rejects_large_payload_when_size_metadata_is_unavailable():
    upload = FakeUpload("large.txt", data=b"x" * (MAX_UPLOAD_BYTES + 1))
    upload.size = None

    with pytest.raises(ValueError, match="10 MiB"):
        extract_uploaded_text(upload)


def test_caps_extracted_plain_text():
    source = "A" * (MAX_DOCUMENT_CHARS + 500)
    upload = FakeUpload("notes.txt", data=source.encode("utf-8"))

    result = extract_uploaded_text(upload)

    assert len(result) == MAX_DOCUMENT_CHARS
    assert result == source[:MAX_DOCUMENT_CHARS]


def test_rejects_unlisted_file_types():
    upload = FakeUpload("archive.zip", data=b"not a supported study file")

    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_uploaded_text(upload)
