from core.topic_extractor import _is_heading, _extract_sections
def test_source_line_numbers_are_recorded():
    source = (
        "مقدمه\n"
        "ماده ۱\n"
        "متن ماده اول\n"
        "ماده ۲\n"
        "متن ماده دوم"
    )

    sections = _extract_sections(source)

    assert sections[0]["source_location"] == "خطوط 2-3"
    assert sections[1]["source_location"] == "خطوط 4-5"