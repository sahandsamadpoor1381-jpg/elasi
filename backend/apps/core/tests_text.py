"""
Persian text normalization tests.

Search must survive the spelling variations Persian shoppers actually
type: Arabic yeh/kaf forms, Persian/Arabic digits, ZWNJ and repeated
whitespace, tatweel padding, and case in Latin brand names.
"""

from __future__ import annotations

from django.test import SimpleTestCase

from apps.core.text import normalize_fa, search_terms


class NormalizeFaTests(SimpleTestCase):
    def test_arabic_yeh_and_kaf_fold_to_persian(self):
        self.assertEqual(normalize_fa("يكي"), normalize_fa("یکی"))
        self.assertEqual(normalize_fa("كتاب"), normalize_fa("کتاب"))

    def test_arabic_alef_forms_fold(self):
        self.assertEqual(normalize_fa("أحمد"), normalize_fa("احمد"))
        self.assertEqual(normalize_fa("إسماعيل"), normalize_fa("اسماعیل"))
        self.assertEqual(normalize_fa("آینه"), normalize_fa("اینه"))

    def test_persian_and_arabic_digits_fold_to_ascii(self):
        self.assertEqual(normalize_fa("۱۲۳"), "123")
        self.assertEqual(normalize_fa("٤٥٦"), "456")

    def test_zwnj_becomes_a_word_boundary(self):
        self.assertEqual(normalize_fa("نیم‌ست"), "نیم ست")

    def test_whitespace_is_collapsed_and_trimmed(self):
        self.assertEqual(
            normalize_fa("  انگشتر    طلا  "),
            "انگشتر طلا",
        )

    def test_tatweel_is_removed(self):
        self.assertEqual(normalize_fa("طـــلا"), "طلا")

    def test_latin_is_case_folded(self):
        self.assertEqual(normalize_fa("ELASI Gold"), "elasi gold")

    def test_none_and_empty_values_are_safe(self):
        self.assertEqual(normalize_fa(None), "")
        self.assertEqual(normalize_fa(""), "")
        self.assertEqual(normalize_fa("   "), "")

    def test_normalization_is_idempotent(self):
        once = normalize_fa("نیم‌ست يكی ۱۲۳")

        self.assertEqual(normalize_fa(once), once)


class SearchTermsTests(SimpleTestCase):
    def test_terms_are_split_for_and_matching(self):
        self.assertEqual(
            search_terms("انگشتر طلا"),
            ["انگشتر", "طلا"],
        )

    def test_empty_query_yields_no_terms(self):
        self.assertEqual(search_terms("   "), [])
        self.assertEqual(search_terms(None), [])

    def test_digit_and_letter_variants_are_unified(self):
        self.assertEqual(
            search_terms("۱۲۳ يكي"),
            ["123", "یکی"],
        )
