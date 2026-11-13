
# -*- coding: utf-8 -*-
"""صفحات اصلی و اتصال منوی بخش‌های حقوقی دادوند."""

import streamlit as st

from core.legal_answer import answer_from_archive
from ui.navigation import render_navigation, get_section_name


# -------------------------------------------------
# نمایش وضعیت بایگانی
# -------------------------------------------------

def _show_archive_status(db):
    st.subheader("وضعیت بایگانی")

    try:
        status = db.get_archive_status()

        if not isinstance(status, dict):
            st.info("اطلاعات وضعیت بایگانی در دسترس نیست.")
            return

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "منابع ثبت‌شده",
            status.get("sources", 0),
        )
        col2.metric(
            "اسناد استخراج‌شده",
            status.get("documents", 0),
        )
        col3.metric(
            "موضوعات حقوقی",
            status.get("legal_topics", 0),
        )

        needs_review = status.get("needs_review", 0)
        if needs_review:
            st.warning(
                f"{needs_review} مورد نیازمند بررسی و تأیید است."
            )

    except Exception as exc:
        st.error(f"خطا در دریافت وضعیت بایگانی: {exc}")


# -------------------------------------------------
# نمایش نتایج جست‌وجو
# -------------------------------------------------

def _show_search_results(result):
    if not isinstance(result, dict):
        st.error("ساختار پاسخ جست‌وجو معتبر نیست.")
        return

    if not result.get("found"):
        st.warning(
            result.get(
                "message",
                "مطلب موردنظر در منابع ثبت‌شده بایگانی پیدا نشد.",
            )
        )
        return

    st.success(
        result.get(
            "message",
            "نتایج مستند در بایگانی پیدا شد.",
        )
    )

    sources = result.get("sources", [])

    for index, source in enumerate(sources, start=1):
        with st.expander(
            f"{index}. {source.get('title') or 'بدون عنوان'}",
            expanded=(index == 1),
        ):
            st.write(
                f"**دسته‌بندی:** "
                f"{source.get('category') or 'ثبت نشده'}"
            )

            st.write(
                f"**نام منبع:** "
                f"{source.get('source_name') or 'ثبت نشده'}"
            )

            st.write(
                f"**نوع منبع:** "
                f"{source.get('source_type') or 'ثبت نشده'}"
            )

            if source.get("source_url"):
                st.write(
                    f"**نشانی منبع:** {source['source_url']}"
                )

            if source.get("page_number") is not None:
                st.write(
                    f"**شماره صفحه:** {source['page_number']}"
                )

            st.markdown("**متن استخراج‌شده از منبع:**")

            exact_text = source.get("exact_text") or ""

            if exact_text.strip():
                st.text_area(
                    "متن منبع",
                    value=exact_text,
                    height=250,
                    key=f"source_text_{index}_{source.get('document_id')}",
                    disabled=True,
                    label_visibility="collapsed",
                )
            else:
                st.warning(
                    "برای این نتیجه، متن رسمی قابل نمایش ثبت نشده است."
                )


# -------------------------------------------------
# جست‌وجوی حقوقی
# -------------------------------------------------

def _render_search(db, category=None):
    st.subheader("جست‌وجوی منابع حقوقی")

    with st.form("legal_search_form"):
        question = st.text_input(
            "عبارت یا پرسش حقوقی",
            placeholder="عبارت موردنظر را وارد کنید...",
        )

        submitted = st.form_submit_button(
            "جست‌وجو",
            use_container_width=True,
        )

    if submitted:
        if not question.strip():
            st.warning("ابتدا عبارت یا پرسش خود را وارد کنید.")
            return

        try:
            with st.spinner("در حال جست‌وجو در بایگانی..."):
                result = answer_from_archive(
                    question=question.strip(),
                    limit=10,
                    category=category,
                    db=db,
                )

            _show_search_results(result)

        except Exception as exc:
            st.error("جست‌وجو با خطا مواجه شد.")
            st.exception(exc)


# -------------------------------------------------
# ورود فایل
# -------------------------------------------------

def _render_file_import(archive):
    st.subheader("ثبت فایل در بایگانی")

    uploaded_file = st.file_uploader(
        "فایل منبع حقوقی را انتخاب کنید",
        type=[
            "pdf",
            "docx",
            "png",
            "jpg",
            "jpeg",
            "tif",
            "tiff",
            "webp",
            "bmp",
        ],
    )

    category = st.selectbox(
        "دسته‌بندی منبع",
        [
            "حقوق مدنی",
            "آیین دادرسی مدنی",
            "حقوق تجارت",
            "حقوق جزا",
            "آیین دادرسی کیفری",
            "نظریات مشورتی",
            "آرای وحدت رویه",
            "آرای قضایی",
            "سایر قوانین",
        ],
    )

    if st.button(
        "ثبت و استخراج متن",
        use_container_width=True,
        disabled=uploaded_file is None,
    ):
        try:
            with st.spinner("در حال ثبت و استخراج فایل..."):
                result = archive.import_source(
                    uploaded_file,
                    category=category,
                )

            if result.get("success"):
                st.success(result.get("message", "فایل ثبت شد."))

                if result.get("character_count") is not None:
                    st.write(
                        f"تعداد نویسه‌های استخراج‌شده: "
                        f"{result['character_count']}"
                    )

                if result.get("text_quality"):
                    st.write(
                        f"کیفیت متن استخراج‌شده: "
                        f"{result['text_quality']}"
                    )

            else:
                st.error(
                    result.get("message", "ثبت فایل ناموفق بود.")
                )

        except Exception as exc:
            st.error("ثبت فایل با خطا مواجه شد.")
            st.exception(exc)


# -------------------------------------------------
# ورود منبع اینترنتی
# -------------------------------------------------

def _render_url_import(archive):
    st.subheader("ثبت منبع اینترنتی")

    with st.form("url_import_form"):
        url = st.text_input(
            "نشانی اینترنتی منبع",
            placeholder="https://example.com/document",
        )

        category = st.selectbox(
            "دسته‌بندی منبع اینترنتی",
            [
                "حقوق مدنی",
                "آیین دادرسی مدنی",
                "حقوق تجارت",
                "حقوق جزا",
                "آیین دادرسی کیفری",
                "نظریات مشورتی",
                "آرای وحدت رویه",
                "آرای قضایی",
                "سایر قوانین",
            ],
            key="url_category",
        )

        submitted = st.form_submit_button(
            "ثبت و استخراج متن URL",
            use_container_width=True,
        )

    if submitted:
        if not url.strip():
            st.warning("نشانی اینترنتی را وارد کنید.")
            return

        try:
            with st.spinner("در حال دریافت و استخراج متن صفحه..."):
                result = archive.import_source(
                    url.strip(),
                    category=category,
                )

            if result.get("success"):
                st.success(result.get("message", "منبع ثبت شد."))

                if result.get("character_count") is not None:
                    st.write(
                        f"تعداد نویسه‌های استخراج‌شده: "
                        f"{result['character_count']}"
                    )
            else:
                st.error(
                    result.get("message", "ثبت منبع ناموفق بود.")
                )

        except Exception as exc:
            st.error("ثبت URL با خطا مواجه شد.")
            st.exception(exc)


# -------------------------------------------------
# صفحه خانه
# -------------------------------------------------

def _render_home(db, archive):
    st.title("دادوند")
    st.caption("سامانه مطالعه و بایگانی منابع حقوقی")

    _show_archive_status(db)

    st.divider()

    tab_search, tab_file, tab_url = st.tabs(
        [
            "جست‌وجوی حقوقی",
            "ورود فایل",
            "ورود URL",
        ]
    )

    with tab_search:
        _render_search(db)

    with tab_file:
        _render_file_import(archive)

    with tab_url:
        _render_url_import(archive)


# -------------------------------------------------
# صفحات بخش‌های حقوقی
# -------------------------------------------------

def _render_legal_section(db, section_key):
    section_name = get_section_name(section_key)

    st.title(section_name)

    st.caption(
        "جست‌وجو فقط در منابع ثبت‌شده و قابل استناد بایگانی انجام می‌شود."
    )

    _render_search(
        db=db,
        category=section_name,
    )


# -------------------------------------------------
# نقطه اتصال صفحات به برنامه
# -------------------------------------------------

def render_pages(db, archive):
    selected_section = render_navigation()

    if selected_section == "home":
        _render_home(db, archive)
    else:
        _render_legal_section(
            db=db,
            section_key=selected_section,
        )
