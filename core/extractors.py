# -*- coding: utf-8 -*-
"""
extractors.py
استخراج متن از DOCX، PDF و تصاویر برای بایگانی حقوقی دادوند.

DOCX: استخراج مستقیم XML
PDF: استخراج با PyMuPDF و OCR در صورت نیاز
Images: OCR با Pillow و pytesseract
"""

from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}

SUPPORTED_IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg",
    ".tif", ".tiff", ".webp", ".bmp"
}

OCR_LANGUAGE = "fas+eng"
OCR_DPI = 250


def _paragraph_text(element):
    """استخراج متن پاراگراف با حفظ شکست خط و تب."""

    parts = []

    for node in element.iter():
        if node.tag in {
            f"{{{W_NS}}}t",
            f"{{{W_NS}}}delText",
        }:
            parts.append(node.text or "")

        elif node.tag == f"{{{W_NS}}}tab":
            parts.append("\t")

        elif node.tag in {
            f"{{{W_NS}}}br",
            f"{{{W_NS}}}cr",
        }:
            parts.append("\n")

    return "".join(parts)


def _extract_table_row(row):
    """استخراج یک ردیف جدول Word."""

    cells = []

    for cell in row.findall("w:tc", NS):
        paragraphs = []

        for paragraph in cell.findall("w:p", NS):
            paragraphs.append(_paragraph_text(paragraph))

        cells.append("\n".join(paragraphs))

    return " | ".join(cells)


class TextExtractor:

    @staticmethod
    def extract_docx(file_path):
        path = Path(file_path)

        if not path.is_file() or path.suffix.lower() != ".docx":
            return {
                "success": False,
                "error": "فایل معتبر DOCX انتخاب نشده است.",
                "paragraphs": [],
                "text": "",
            }

        paragraphs = []
        paragraph_number = 0
        table_number = 0

        try:
            with zipfile.ZipFile(str(path), "r") as archive:

                if "word/document.xml" not in archive.namelist():
                    return {
                        "success": False,
                        "error": "ساختار سند DOCX معتبر نیست.",
                        "paragraphs": [],
                        "text": "",
                    }

                root = ET.fromstring(
                    archive.read("word/document.xml")
                )

                body = root.find("w:body", NS)

                if body is None:
                    return {
                        "success": False,
                        "error": "بدنه سند Word پیدا نشد.",
                        "paragraphs": [],
                        "text": "",
                    }

                # ترتیب اصلی پاراگراف‌ها و جدول‌ها حفظ می‌شود.
                for child in list(body):

                    if child.tag == f"{{{W_NS}}}p":

                        paragraph_number += 1

                        value = _paragraph_text(child)

                        # حتی پاراگراف خالی نیز حفظ می‌شود.
                        paragraphs.append({
                            "paragraph_number": paragraph_number,
                            "text": value,
                            "element_type": "paragraph",
                            "extraction_method": "docx-xml",
                        })

                    elif child.tag == f"{{{W_NS}}}tbl":

                        table_number += 1

                        for row_number, row in enumerate(
                            child.findall("w:tr", NS),
                            start=1,
                        ):

                            row_text = _extract_table_row(row)

                            paragraphs.append({
                                "paragraph_number": None,
                                "table_number": table_number,
                                "row_number": row_number,
                                "text": row_text,
                                "element_type": "table_row",
                                "extraction_method": "docx-xml-table",
                            })

            extracted_text = "\n".join(
                item["text"] for item in paragraphs
            )

            if not extracted_text.strip():
                return {
                    "success": False,
                    "error": "متن قابل‌استخراج در DOCX پیدا نشد.",
                    "paragraphs": paragraphs,
                    "text": "",
                }

            return {
                "success": True,
                "error": None,
                "paragraphs": paragraphs,
                "text": extracted_text,
                "extraction_method": "docx-xml",
            }

        except zipfile.BadZipFile:
            return {
                "success": False,
                "error": "فایل DOCX سالم نیست.",
                "paragraphs": [],
                "text": "",
            }

        except ET.ParseError as exc:
            return {
                "success": False,
                "error": f"خطای خواندن XML سند: {exc}",
                "paragraphs": [],
                "text": "",
            }

        except Exception as exc:
            return {
                "success": False,
                "error": f"خطا در استخراج DOCX: {exc}",
                "paragraphs": [],
                "text": "",
            }

    @staticmethod
    def _ocr_image(image, language=OCR_LANGUAGE):
        """استخراج متن از تصویر با OCR."""

        try:
            import pytesseract

            return pytesseract.image_to_string(
                image,
                lang=language,
            )

        except ImportError as exc:
            raise RuntimeError(
                "کتابخانه pytesseract نصب نیست."
            ) from exc

        except Exception as exc:
            raise RuntimeError(
                "اجرای OCR ناموفق بود. "
                "نصب Tesseract و زبان فارسی fas را بررسی کنید: "
                f"{exc}"
            ) from exc

    @classmethod
    def extract_pdf(
        cls,
        file_path,
        ocr=True,
        language=OCR_LANGUAGE,
        dpi=OCR_DPI,
    ):
        """استخراج متن PDF با OCR برای صفحات اسکن‌شده."""

        path = Path(file_path)

        if not path.is_file() or path.suffix.lower() != ".pdf":
            return {
                "success": False,
                "error": "فایل معتبر PDF انتخاب نشده است.",
                "pages": [],
                "text": "",
            }

        try:
            import fitz

        except ImportError:
            return {
                "success": False,
                "error": (
                    "کتابخانه PyMuPDF نصب نیست. "
                    "دستور نصب: pip install PyMuPDF"
                ),
                "pages": [],
                "text": "",
            }

        pages = []

        try:
            with fitz.open(str(path)) as document:

                if document.is_encrypted:
                    return {
                        "success": False,
                        "error": "PDF رمزگذاری شده است.",
                        "pages": [],
                        "text": "",
                    }

                for index, page in enumerate(document):

                    # استخراج متن اصلی صفحه
                    page_text = page.get_text("text") or ""

                    method = "pymupdf-text"

                    # OCR فقط وقتی متن قابل‌استخراج وجود ندارد.
                    if not page_text.strip() and ocr:

                        try:
                            from PIL import Image
                            import io

                            scale = dpi / 72

                            matrix = fitz.Matrix(
                                scale,
                                scale,
                            )

                            pixmap = page.get_pixmap(
                                matrix=matrix,
                                alpha=False,
                            )

                            image_bytes = pixmap.tobytes("png")

                            with Image.open(
                                io.BytesIO(image_bytes)
                            ) as image:

                                page_text = cls._ocr_image(
                                    image,
                                    language,
                                )

                            method = "tesseract-ocr"

                        except Exception as exc:
                            page_text = ""

                            method = (
                                f"ocr-failed: {exc}"
                            )

                    # صفحات خالی نیز حفظ می‌شوند.
                    pages.append({
                        "page_number": index + 1,
                        "text": page_text,
                        "extraction_method": method,
                    })

            extracted_text = "\n\n".join(
                f"[صفحه {item['page_number']}]\n{item['text']}"
                for item in pages
            )

            if not any(
                item["text"].strip()
                for item in pages
            ):
                return {
                    "success": False,
                    "error": (
                        "متنی از PDF استخراج نشد. "
                        "OCR، کیفیت فایل و زبان فارسی را بررسی کنید."
                    ),
                    "pages": pages,
                    "text": "",
                }

            return {
                "success": True,
                "error": None,
                "pages": pages,
                "text": extracted_text,
                "extraction_method": "pymupdf-with-ocr-fallback",
            }

        except Exception as exc:
            return {
                "success": False,
                "error": f"خطا در خواندن PDF: {exc}",
                "pages": pages,
                "text": "",
            }

    @classmethod
    def extract_image(
        cls,
        file_path,
        language=OCR_LANGUAGE,
    ):
        """استخراج متن تصاویر با OCR."""

        path = Path(file_path)

        if (
            not path.is_file()
            or path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS
        ):
            return {
                "success": False,
                "error": "فایل تصویر معتبر انتخاب نشده است.",
                "text": "",
            }

        try:
            from PIL import Image

            with Image.open(str(path)) as image:

                # تبدیل تصویر به حالت مناسب OCR
                if image.mode not in {"RGB", "L"}:
                    image = image.convert("RGB")

                text = cls._ocr_image(
                    image,
                    language,
                )

            if not text.strip():
                return {
                    "success": False,
                    "error": (
                        "متنی تشخیص داده نشد. "
                        "کیفیت تصویر و زبان فارسی OCR را بررسی کنید."
                    ),
                    "text": "",
                }

            return {
                "success": True,
                "error": None,
                "text": text,
                "extraction_method": "tesseract-ocr",
            }

        except ImportError:
            return {
                "success": False,
                "error": (
                    "برای OCR تصویر، Pillow و pytesseract "
                    "باید نصب باشند."
                ),
                "text": "",
            }

        except Exception as exc:
            return {
                "success": False,
                "error": f"خطای OCR تصویر: {exc}",
                "text": "",
            }

    @classmethod
    def extract_file(cls, file_path):
        """تشخیص نوع فایل و اجرای استخراج مناسب."""

        path = Path(file_path)

        if not path.is_file():
            return {
                "success": False,
                "error": "فایل پیدا نشد.",
                "text": "",
            }

        extension = path.suffix.lower()

        if extension == ".docx":
            return cls.extract_docx(path)

        if extension == ".pdf":
            return cls.extract_pdf(path)

        if extension in SUPPORTED_IMAGE_EXTENSIONS:
            return cls.extract_image(path)

        return {
            "success": False,
            "error": f"نوع فایل پشتیبانی نمی‌شود: {extension}",
            "text": "",
        }