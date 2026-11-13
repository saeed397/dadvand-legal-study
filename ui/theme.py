
# -*- coding: utf-8 -*-
"""مدیریت ظاهر و تنظیمات نمایشی دادوند."""

import streamlit as st


def apply_theme():
    """اعمال تنظیمات ظاهری بر اساس انتخاب کاربر."""

    if "app_theme" not in st.session_state:
        st.session_state["app_theme"] = "dark"

    theme = st.session_state["app_theme"]

    if theme == "light":
        background = "#FFFFFF"
        secondary = "#F3F5F7"
        text = "#20252B"
        border = "#D9DEE5"
    else:
        background = "#101820"
        secondary = "#1B2833"
        text = "#F2F2F2"
        border = "#354452"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {background};
            color: {text};
            direction: rtl;
            text-align: right;
        }}

        [data-testid="stSidebar"] {{
            background-color: {secondary};
            direction: rtl;
        }}

        .stMarkdown, .stText, label, p {{
            text-align: right;
        }}

        input, textarea {{
            direction: rtl !important;
            text-align: right !important;
        }}

        div[data-testid="stExpander"] {{
            border: 1px solid {border};
            border-radius: 10px;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


def render_theme_selector():
    """نمایش انتخاب‌گر حالت روشن و تاریک."""

    current = st.session_state.get("app_theme", "dark")

    selected = st.radio(
        "حالت نمایش",
        options=["dark", "light"],
        format_func=lambda value: (
            "تیره" if value == "dark" else "روشن"
        ),
        index=0 if current == "dark" else 1,
        horizontal=True,
        key="theme_selector",
    )

    if selected != current:
        st.session_state["app_theme"] = selected
        st.rerun()
