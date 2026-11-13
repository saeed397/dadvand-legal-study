
# -*- coding: utf-8 -*-
"""آزمون‌های استخراج متن از اسناد دادوند."""

import zipfile

from core.extractors import TextExtractor


def create_test_docx(path):
    """ساخت یک فایل DOCX آزمایشی بدون نیاز به کتابخانه خارجی."""

    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <w:document
      xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:body>
        <w:p>
          <w:r><w:t>ماده آزمایشی اول</w:t></w:r>
        </w:p>
        <w:p>
          <w:r><w:t>متن آزمایشی حقوقی</w:t></w:r>
        </w:p>
        <w:sectPr/>
      </w:body>
    </w:document>
    """

    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "word/document.xml",
            document_xml,
        )


def test_docx_text_extraction(tmp_path):
    file_path = tmp_path / "test.docx"
    create_test_docx(file_path)

    result = TextExtractor.extract_docx(file_path)

    assert result["success"] is True

    extracted = "\n".join(
        item["text"]
        for item in result["paragraphs"]
    )

    assert "ماده آزمایشی اول" in extracted
    assert "متن آزمایشی حقوقی" in extracted


def test_invalid_docx_path():
    result = TextExtractor.extract_docx(
        "missing_test_file.docx"
    )

    assert result["success"] is False


def test_empty_url_is_rejected(tmp_path):
    from core.ingestion import DocumentIngestion

    ingestion = DocumentIngestion(tmp_path)

    result = ingestion.extract_url_text("")

    assert result["success"] is False
    assert result["text"] == ""
    assert result["error"]