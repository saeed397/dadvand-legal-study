# -*- coding: utf-8 -*-
"""آزمون‌های دریافت و استخراج منابع حقوقی دادوند."""

from core.ingestion import DocumentIngestion, WebTextParser


def test_supported_file_extensions(tmp_path):
    ingestion = DocumentIngestion(tmp_path)

    for extension in (
        ".pdf",
        ".docx",
        ".png",
        ".jpg",
        ".jpeg",
        ".tif",
        ".tiff",
        ".webp",
    ):
        file_path = tmp_path / f"sample{extension}"
        file_path.write_bytes(b"test")

        valid, _ = ingestion.validate_file(file_path)

        assert valid is True


def test_empty_file_is_rejected(tmp_path):
    ingestion = DocumentIngestion(tmp_path)
    file_path = tmp_path / "empty.pdf"
    file_path.write_bytes(b"")

    valid, message = ingestion.validate_file(file_path)

    assert valid is False
    assert "خالی" in message


def test_unsupported_extension_is_rejected(tmp_path):
    ingestion = DocumentIngestion(tmp_path)
    file_path = tmp_path / "sample.txt"
    file_path.write_text("test", encoding="utf-8")

    valid, _ = ingestion.validate_file(file_path)

    assert valid is False


def test_missing_file_is_rejected(tmp_path):
    ingestion = DocumentIngestion(tmp_path)

    valid, _ = ingestion.validate_file(
        tmp_path / "missing.pdf"
    )

    assert valid is False


def test_empty_url_is_rejected(tmp_path):
    ingestion = DocumentIngestion(tmp_path)

    valid, _ = ingestion.validate_url("")

    assert valid is False


def test_invalid_url_scheme_is_rejected(tmp_path):
    ingestion = DocumentIngestion(tmp_path)

    valid, _ = ingestion.validate_url(
        "ftp://example.com/file"
    )

    assert valid is False


def test_html_parser_extracts_text():
    parser = WebTextParser()

    parser.feed(
        "<html><body>"
        "<h1>عنوان آزمایشی</h1>"
        "<p>متن حقوقی آزمایشی</p>"
        "<script>مطلب غیرقابل استخراج</script>"
        "</body></html>"
    )

    extracted = parser.get_text()

    assert "عنوان آزمایشی" in extracted
    assert "متن حقوقی آزمایشی" in extracted
    assert "مطلب غیرقابل استخراج" not in extracted


def test_process_source_rejects_missing_file(tmp_path):
    ingestion = DocumentIngestion(tmp_path)

    result = ingestion.process_source(
        tmp_path / "missing.pdf"
    )

    assert result["success"] is False
    assert result["text"] == ""