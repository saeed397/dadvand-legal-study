
# -*- coding: utf-8 -*-
"""استخراج ساختاری موضوعات از اسناد بایگانی دادوند.

این فایل هیچ محتوای حقوقی تولید نمی‌کند.
متن منبع عیناً حفظ می‌شود و تا بررسی انسانی، متن رسمی تأییدشده نیست.
"""

import re
from typing import Dict, List, Optional

try:
    from .database import LegalDatabase
except ImportError:
    from database import LegalDatabase


_ARTICLE_RE = re.compile(
    r'^\s*(?:ماده\s*[۱۲۳۴۵۶۷۸۹۰0-9]+|ماده\s*\([^)]+\))',
    re.IGNORECASE
)

_NUMBERED_HEADING_RE = re.compile(
    r'^\s*(?:[0-9۰-۹]+\s*[.)ـ-]|[۰-۹]+️⃣|[🔹🔸▪◾●■◆])\s*\S.{0,180}$'
)

_HEADING_END_RE = re.compile(
    r'^\s*\S.{2,180}[:：]\s*$'
)


def _clean_line(line: str) -> str:
    """پاک‌سازی فقط برای تشخیص و نمایش عنوان؛ نه متن اصلی."""
    return re.sub(
        r'[ \t]+',
        ' ',
        (line or '').replace('\ufeff', '')
    ).strip()


def _is_heading(line: str) -> bool:
    """تشخیص سرعنوان‌های احتمالی بدون تفسیر محتوای حقوقی."""

    line = _clean_line(line)

    if not line or len(line) > 200:
        return False

    if line.startswith(('با احترام', 'سلام', 'درود')):
        return False

    if _ARTICLE_RE.match(line):
        return True

    if _NUMBERED_HEADING_RE.match(line):
        return True

    if _HEADING_END_RE.match(line) and len(line.split()) <= 18:
        return True

    return False


def _extract_sections(text: str) -> List[Dict[str, str]]:
    """استخراج بخش‌ها با حفظ دقیق متن و خطوط منبع."""

    if not text:
        return []

    # حفظ جداکننده‌های اصلی خطوط، از جمله CRLF و LF
    lines = text.splitlines(keepends=True)

    # نسخه بدون پایان خط فقط برای تشخیص سرعنوان
    detection_lines = [
        line.rstrip('\r\n') for line in lines
    ]

    starts = [
        i for i, line in enumerate(detection_lines)
        if _is_heading(line)
    ]

    sections = []

    for index, start in enumerate(starts):

        end = (
            starts[index + 1]
            if index + 1 < len(starts)
            else len(lines)
        )

        # عنوان فقط برای نمایش پاک‌سازی می‌شود
        title = _clean_line(detection_lines[start])
        title = title.rstrip(':：').strip()

        # متن منبع بدون حذف خط خالی یا تغییر فاصله‌ها
        source_excerpt = ''.join(lines[start:end])

        if not title or not source_excerpt.strip():
            continue

        sections.append({
            'title': title[:250],
            'official_text': source_excerpt,
            'source_location': (
                f'خطوط {start + 1}-{max(start + 1, end)}'
            ),
        })

    return sections


def extract_topics_from_document(
    document_id: int,
    db: Optional[LegalDatabase] = None,
    save: bool = True,
) -> Dict[str, object]:
    """استخراج موضوعات از یک سند مشخص."""

    db = db or LegalDatabase()

    with db._connect() as conn:
        row = conn.execute(
            '''
            SELECT id, title, category, extracted_text
            FROM documents
            WHERE id = ?
            ''',
            (int(document_id),)
        ).fetchone()

        if row is None:
            raise ValueError(
                f'سند با شناسه {document_id} پیدا نشد.'
            )

        document = dict(row)

    sections = _extract_sections(
        document.get('extracted_text') or ''
    )

    saved_ids = []
    duplicates = 0

    if save:

        for section in sections:

            with db._connect() as conn:
                existing = conn.execute(
                    '''
                    SELECT id
                    FROM legal_topics
                    WHERE source_document_id = ?
                      AND title = ?
                      AND source_location = ?
                      AND official_text = ?
                    LIMIT 1
                    ''',
                    (
                        document_id,
                        section['title'],
                        section['source_location'],
                        section['official_text'],
                    )
                ).fetchone()

            if existing:
                duplicates += 1
                saved_ids.append(existing['id'])
                continue

            topic_id = db.add_legal_topic(
                title=section['title'],
                category=document['category'],
                subject=None,
                official_text=section['official_text'],
                official_text_status='source_excerpt_unverified',
                plain_explanation='',
                hypothetical_court_example='',
                mcq_items=[],
                source_document_id=int(document_id),
                source_location=section['source_location'],
                review_status='needs_review',
            )

            saved_ids.append(topic_id)

    return {
        'document_id': int(document_id),
        'document_title': document['title'],
        'sections_found': len(sections),
        'saved_or_existing_topic_ids': saved_ids,
        'duplicates_skipped': duplicates,
        'saved': bool(save),
        'sections': sections,
        'notice': (
            'متن استخراج‌شده عیناً از سند منبع برداشته شده است. '
            'تأیید رسمی بودن متن، توضیح، مثال و تست‌ها نیازمند '
            'بررسی مستند انسانی است. هیچ محتوای حقوقی تازه‌ای '
            'تولید نشده است.'
        ),
    }


def extract_all_documents(
    db: Optional[LegalDatabase] = None,
    save: bool = True
) -> List[Dict[str, object]]:
    """استخراج موضوعات از تمام اسناد بایگانی."""

    db = db or LegalDatabase()

    with db._connect() as conn:
        rows = conn.execute(
            'SELECT id FROM documents ORDER BY id'
        ).fetchall()

    results = []

    for row in rows:
        results.append(
            extract_topics_from_document(
                row['id'],
                db=db,
                save=save
            )
        )

    return results


if __name__ == '__main__':

    database = LegalDatabase()

    print('آزمایش استخراج موضوعات حقوقی دادوند')
    print('حالت اجرا: پیش‌نمایش بدون ذخیره\n')

    with database._connect() as conn:
        documents = conn.execute(
            'SELECT id, title FROM documents ORDER BY id'
        ).fetchall()

    if not documents:
        print('هیچ سندی در بایگانی وجود ندارد.')

    else:
        for document in documents:

            print('\n' + '=' * 50)
            print(
                f"سند {document['id']}: "
                f"{document['title']}"
            )

            result = extract_topics_from_document(
                document['id'],
                db=database,
                save=False
            )

            print(
                'تعداد موضوعات شناسایی‌شده:',
                result['sections_found']
            )

            for section in result['sections']:
                print(
                    '-',
                    section['title'],
                    '|',
                    section['source_location']
                )

        print('\nپیش‌نمایش تمام شد؛ هیچ رکوردی ذخیره نشد.')
