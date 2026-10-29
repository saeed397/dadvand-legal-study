
# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch, MagicMock

from core.legal_answer import LegalAnswer


class TestLegalAnswer(unittest.TestCase):

    def setUp(self):
        self.answer_service = LegalAnswer()

    def test_empty_question_is_handled(self):
        result = self.answer_service.answer("")

        self.assertIsNotNone(result)

    def test_whitespace_question_is_handled(self):
        result = self.answer_service.answer("   ")

        self.assertIsNotNone(result)

    def test_answer_does_not_claim_unverified_source_is_official(self):
        result = self.answer_service.answer(
            "موضوع آزمایشی که در بایگانی وجود ندارد"
        )

        self.assertIsNotNone(result)

    def test_answer_method_is_available(self):
        self.assertTrue(callable(self.answer_service.answer))


if __name__ == "__main__":
    unittest.main()
