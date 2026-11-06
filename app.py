
# -*- coding: utf-8 -*-

import streamlit as st

from core.database import LegalDatabase
from core.archive_manager import ArchiveManager

from ui.pages import render_pages
from ui.theme import apply_theme, render_theme_selector


st.set_page_config(
    page_title="دادوند | مطالعه حقوق",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_home_settings():
    """نمایش تنظیمات فقط در صفحه خانه."""

    with st.expander("⚙️ تنظیمات دادوند", expanded=False):

        st.subheader("تنظیمات ظاهر")
        render_theme_selector()


def main():

    # ساخت پایگاه داده
    db = LegalDatabase()

    # ساخت مدیر بایگانی با اتصال به همان پایگاه داده
    archive = ArchiveManager(db=db)

    # اعمال پوسته
    apply_theme()

    # عنوان منوی کناری
    with st.sidebar:
        st.title("⚖️ دادوند")
        st.caption("سامانه مطالعه و بایگانی منابع حقوقی")
        st.divider()

    # نمایش صفحات و منوی اصلی
    render_pages(db, archive)

    # تنظیمات فقط در صفحه خانه
    if st.session_state.get("legal_navigation") == "خانه":
        st.divider()
        render_home_settings()

    # پاورقی
    st.divider()
    st.caption(
        "دادوند | پاسخ‌ها باید بر اساس منابع ثبت‌شده در بایگانی باشند."
    )


if __name__ == "__main__":
    main()
