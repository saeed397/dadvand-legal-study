# -*- coding: utf-8 -*-
"""دریافت و استخراج متن منابع حقوقی برای بایگانی دادوند."""

from pathlib import Path
from urllib.parse import urlparse, urljoin
from urllib.request import (
    Request,
    build_opener,
    HTTPRedirectHandler,
)
from urllib.error import HTTPError, URLError
from html.parser import HTMLParser

import ipaddress
import socket
import re


try:
    from .extractors import TextExtractor
except ImportError:
    try:
        from extractors import TextExtractor
    except ImportError:
        TextExtractor = None


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".webp",
    ".bmp",
}

MAX_URL_BYTES = 5 * 1024 * 1024
URL_TIMEOUT_SECONDS = 20
MAX_REDIRECTS = 5


class NoRedirectHandler(HTTPRedirectHandler):
    """جلوگیری از تغییرمسیر خودکار برای اعتبارسنجی مقصد."""

    def redirect_request(
        self, req, fp, code, msg, headers, newurl
    ):
        return None


class WebTextParser(HTMLParser):
    SKIP_TAGS = {
        "script", "style", "noscript", "svg",
        "nav", "footer", "header", "aside",
        "canvas", "template",
    }

    BLOCK_TAGS = {
        "p", "div", "article", "section", "main",
        "h1", "h2", "h3", "h4", "h5", "h6",
        "li", "br", "tr", "blockquote",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()

        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
        elif not self.skip_depth and tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag in self.SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
        elif not self.skip_depth and tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip_depth and data.strip():
            self.parts.append(data.strip())

    def get_text(self):
        value = "\n".join(self.parts)
        value = re.sub(r"[ \t]+", " ", value)
        value = re.sub(r"\n\s*\n+", "\n\n", value)
        return value.strip()


class DocumentIngestion:
    """ورود فایل‌ها و URL به بایگانی؛ بدون حذف فایل اصلی."""

    def __init__(self, inbox_path):
        self.inbox_path = Path(inbox_path)
        self.inbox_path.mkdir(parents=True, exist_ok=True)

    def list_supported_files(self):
        return sorted(
            path
            for path in self.inbox_path.iterdir()
            if path.is_file()
            and path.suffix.lower() in SUPPORTED_EXTENSIONS
        )

    def validate_file(self, file_path):
        try:
            path = Path(file_path)

            if not path.exists():
                return False, "فایل پیدا نشد."

            if not path.is_file():
                return False, "مسیر انتخاب‌شده فایل نیست."

            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                return False, "پسوند فایل پشتیبانی نمی‌شود."

            if path.stat().st_size == 0:
                return False, "فایل خالی است."

            return True, "فایل برای پردازش معتبر است."

        except (OSError, TypeError, ValueError) as exc:
            return False, f"خطا در بررسی فایل: {exc}"

    @staticmethod
    def validate_url(url):
        if not isinstance(url, str) or not url.strip():
            return False, "نشانی URL وارد نشده است."

        try:
            parsed = urlparse(url.strip())

            if parsed.scheme.lower() not in {"http", "https"}:
                return False, "فقط URL با http یا https پذیرفته می‌شود."

            if not parsed.hostname:
                return False, "نام دامنه در URL مشخص نیست."

            if parsed.username or parsed.password:
                return False, "URL دارای نام کاربری یا رمز عبور پذیرفته نمی‌شود."

            port = parsed.port or (
                443 if parsed.scheme.lower() == "https" else 80
            )

            try:
                addresses = {
                    ipaddress.ip_address(parsed.hostname)
                }
            except ValueError:
                addresses = {
                    ipaddress.ip_address(item[4][0].split("%", 1)[0])
                    for item in socket.getaddrinfo(
                        parsed.hostname, port
                    )
                }

            if not addresses:
                return False, "دامنه قابل شناسایی نیست."

            if any(not address.is_global for address in addresses):
                return False, "دسترسی به IP خصوصی یا غیرعمومی مجاز نیست."

            return True, "URL معتبر است."

        except (OSError, ValueError, TypeError) as exc:
            return False, f"URL معتبر نیست: {exc}"

    def extract_url_text(
        self,
        url,
        timeout=URL_TIMEOUT_SECONDS,
        max_bytes=MAX_URL_BYTES,
    ):
        """استخراج متن صفحات عمومی HTML و متن ساده."""

        current_url = url.strip() if isinstance(url, str) else url

        opener = build_opener(NoRedirectHandler())

        headers = {
            "User-Agent": "DadvandLegalArchive/1.0",
            "Accept": "text/html,application/xhtml+xml,text/plain",
        }

        try:
            for redirect_count in range(MAX_REDIRECTS + 1):

                valid, message = self.validate_url(current_url)

                if not valid:
                    return {
                        "success": False,
                        "source_url": current_url,
                        "text": "",
                        "error": message,
                    }

                request = Request(
                    current_url,
                    headers=headers,
                )

                try:
                    response = opener.open(
                        request,
                        timeout=timeout,
                    )

                except HTTPError as exc:
                    if exc.code in {301, 302, 303, 307, 308}:
                        location = exc.headers.get("Location")

                        if not location:
                            return {
                                "success": False,
                                "source_url": current_url,
                                "text": "",
                                "error": "نشانی مقصد تغییرمسیر مشخص نیست.",
                            }

                        if redirect_count >= MAX_REDIRECTS:
                            return {
                                "success": False,
                                "source_url": current_url,
                                "text": "",
                                "error": "تعداد تغییرمسیرها بیش از حد مجاز است.",
                            }

                        current_url = urljoin(current_url, location)
                        continue

                    return {
                        "success": False,
                        "source_url": current_url,
                        "text": "",
                        "error": f"خطای HTTP: {exc.code}",
                    }

                with response:
                    content_type = (
                        response.headers.get_content_type().lower()
                    )

                    charset = (
                        response.headers.get_content_charset()
                        or "utf-8"
                    )

                    data = response.read(max_bytes + 1)

                if len(data) > max_bytes:
                    return {
                        "success": False,
                        "source_url": current_url,
                        "text": "",
                        "error": "حجم صفحه بیش از حد مجاز است.",
                    }

                allowed_types = {
                    "text/html",
                    "application/xhtml+xml",
                    "text/plain",
                }

                if content_type not in allowed_types:
                    return {
                        "success": False,
                        "source_url": current_url,
                        "text": "",
                        "error": (
                            "نوع محتوای URL پشتیبانی نمی‌شود: "
                            + content_type
                        ),
                    }

                page_content = data.decode(
                    charset,
                    errors="replace",
                )

                if content_type == "text/plain":
                    extracted = page_content.strip()
                    method = "text/plain"

                else:
                    parser = WebTextParser()
                    parser.feed(page_content)
                    parser.close()

                    extracted = parser.get_text()
                    method = "html.parser"

                if not extracted:
                    return {
                        "success": False,
                        "source_url": current_url,
                        "text": "",
                        "error": (
                            "متن قابل‌استخراج پیدا نشد؛ "
                            "صفحه ممکن است پویا یا نیازمند ورود باشد."
                        ),
                    }

                return {
                    "success": True,
                    "source_url": current_url,
                    "text": extracted,
                    "error": None,
                    "extraction_method": method,
                    "source_type": "url",
                }

            return {
                "success": False,
                "source_url": current_url,
                "text": "",
                "error": "تعداد تغییرمسیرها بیش از حد مجاز است.",
            }

        except URLError as exc:
            return {
                "success": False,
                "source_url": current_url,
                "text": "",
                "error": f"خطا در اتصال: {exc.reason}",
            }

        except TimeoutError:
            return {
                "success": False,
                "source_url": current_url,
                "text": "",
                "error": "زمان انتظار برای دریافت صفحه تمام شد.",
            }

        except Exception as exc:
            return {
                "success": False,
                "source_url": current_url,
                "text": "",
                "error": f"خطا در دریافت یا استخراج URL: {exc}",
            }

    def extract_file_text(self, file_path):
        path = Path(file_path)

        valid, message = self.validate_file(path)

        if not valid:
            return {
                "success": False,
                "source_path": str(path),
                "text": "",
                "error": message,
            }

        if TextExtractor is None:
            return {
                "success": False,
                "source_path": str(path),
                "text": "",
                "error": "ماژول extractors.py قابل import نیست.",
            }

        try:
            result = TextExtractor.extract_file(str(path))

            if not isinstance(result, dict):
                return {
                    "success": False,
                    "source_path": str(path),
                    "text": "",
                    "error": "خروجی extractors.py معتبر نیست.",
                }

            if not result.get("success"):
                return {
                    **result,
                    "success": False,
                    "source_path": str(path),
                    "source_type": path.suffix.lower().lstrip("."),
                    "text": result.get("text", ""),
                }

            extension = path.suffix.lower()

            if extension == ".docx":
                paragraphs = result.get("paragraphs", [])

                text = "\n".join(
                    item.get("text", "")
                    for item in paragraphs
                )

            elif extension == ".pdf":
                pages = result.get("pages", [])

                text = "\n\n".join(
                    (
                        f"[صفحه {item.get('page_number', '?')}]\n"
                        f"{item.get('text', '')}"
                    )
                    for item in pages
                )

            else:
                text = result.get("text", "")

            if not isinstance(text, str) or not text.strip():
                return {
                    **result,
                    "success": False,
                    "source_path": str(path),
                    "source_type": extension.lstrip("."),
                    "text": "",
                    "error": (
                        result.get("error")
                        or "متن قابل‌استخراجی پیدا نشد."
                    ),
                }

            return {
                **result,
                "success": True,
                "source_path": str(path),
                "source_type": extension.lstrip("."),
                "text": text,
                "error": None,
            }

        except Exception as exc:
            return {
                "success": False,
                "source_path": str(path),
                "source_type": path.suffix.lower().lstrip("."),
                "text": "",
                "error": f"خطا در پردازش فایل: {exc}",
            }

    def process_source(self, source):
        if (
            isinstance(source, str)
            and urlparse(source.strip()).scheme.lower()
            in {"http", "https"}
        ):
            return self.extract_url_text(source)

        return self.extract_file_text(source)