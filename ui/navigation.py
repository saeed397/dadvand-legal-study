
import streamlit as st


LEGAL_SECTIONS = [
    ("dashboard", "خانه"),
    ("civil_law", "حقوق مدنی"),
    ("civil_procedure", "آیین دادرسی مدنی"),
    ("commercial_law", "حقوق تجارت"),
    ("criminal_law", "حقوق جزا"),
    ("criminal_procedure", "آیین دادرسی کیفری"),
    ("legal_opinions", "نظریات مشورتی"),
    ("precedents", "آرای وحدت رویه"),
    ("court_decisions", "آرای قضایی"),
    ("archive", "بایگانی منابع"),
    ("settings", "تنظیمات"),
]


def initialize_navigation():
    if "dadvand_page" not in st.session_state:
        st.session_state["dadvand_page"] = "dashboard"


def render_navigation():
    initialize_navigation()

    st.sidebar.title("دادوند")
    st.sidebar.caption("سامانه مطالعه و بایگانی حقوقی")

    labels = [label for _, label in LEGAL_SECTIONS]
    page_keys = [key for key, _ in LEGAL_SECTIONS]

    current_key = st.session_state["dadvand_page"]

    if current_key not in page_keys:
        current_key = "dashboard"

    current_index = page_keys.index(current_key)

    selected_label = st.sidebar.radio(
        "بخش موردنظر",
        options=labels,
        index=current_index,
        key="dadvand_navigation_radio",
    )

    selected_key = dict(
        (label, key)
        for key, label in LEGAL_SECTIONS
    )[selected_label]

    st.session_state["dadvand_page"] = selected_key

    return selected_key
