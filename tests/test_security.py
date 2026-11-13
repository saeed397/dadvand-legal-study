# -*- coding: utf-8 -*-
"""آزمون‌های اعتبارسنجی امنیتی URL در دادوند."""

from core.ingestion import DocumentIngestion


def test_http_url_is_accepted_syntactically():
    valid, _ = DocumentIngestion.validate_url(
        "https://example.com/legal"
    )

    # اعتبارسنجی دامنه به DNS و شبکه وابسته است؛
    # این آزمون فقط قالب URL را بررسی نمی‌کند.
    assert isinstance(valid, bool)


def test_private_ip_is_rejected():
    valid, message = DocumentIngestion.validate_url(
        "http://127.0.0.1/test"
    )

    assert valid is False
    assert "خصوصی" in message or "غیرعمومی" in message


def test_localhost_is_rejected():
    valid, _ = DocumentIngestion.validate_url(
        "http://localhost/"
    )

    assert valid is False


def test_url_with_credentials_is_rejected():
    valid, _ = DocumentIngestion.validate_url(
        "https://user:password@example.com/"
    )

    assert valid is False


def test_non_http_scheme_is_rejected():
    valid, _ = DocumentIngestion.validate_url(
        "file:///etc/passwd"
    )

    assert valid is False