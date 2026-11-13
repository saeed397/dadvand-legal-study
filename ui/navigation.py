
# -*- coding: utf-8 -*-
"""مدیریت منوی اصلی و بخش‌های حقوقی دادوند."""

import streamlit as st


LEGAL_SECTIONS = {
    "خانه": "home",
    "حقوق مدنی": "civil",
    "آیین دادرسی مدنی": "civil_procedure",
    "حقوق تجارت": "commercial",
    "حقوق جزا": "criminal",
    "آیین دادرسی کیفری": "criminal_procedure",
    "نظریات مشورتی": "advisory_opinions",
    "آرای وحدت رویه": "unity_precedents",
    "آرای قضایی": "judicial_rulings",
}


def render_navigation():
    """نمایش منوی بخش‌های حقوقی."""

    st.sidebar.title("⚖️ دادوند")
    st.sidebar.caption("سامانه مطالعه و بایگانی منابع حقوقی")

    section_names = list(LEGAL_SECTIONS.keys())

    selected_name = st.sidebar.radio(
        "بخش‌های حقوقی",
        options=section_names,
        key="legal_navigation",
    )

    return LEGAL_SECTIONS[selected_name]


def get_section_name(section_key):
    """دریافت عنوان فارسی بخش."""

    for name, key in LEGAL_SECTIONS.items():
        if key == section_key:
            return name

    return "خانه"
