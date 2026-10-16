from django.test import SimpleTestCase

from .validators import (
    InvalidPhoneNumber,
    InvalidPostalCode,
    normalize_digits,
    normalize_iran_phone,
    normalize_iran_postal_code,
    normalize_whitespace,
)


class DigitNormalizationTests(SimpleTestCase):
    def test_persian_digits_convert_to_ascii(self):
        self.assertEqual(
            normalize_digits("۰۹۱۲۱۲۳۴۵۶۷"),
            "09121234567",
        )

    def test_arabic_digits_convert_to_ascii(self):
        self.assertEqual(
            normalize_digits("٠٩١٢١٢٣٤٥٦٧"),
            "09121234567",
        )

    def test_mixed_digits_convert_to_ascii(self):
        self.assertEqual(
            normalize_digits("۰9١2۳456٧89"),
            "09123456789",
        )


class IranPhoneNormalizationTests(SimpleTestCase):
    def test_local_number(self):
        self.assertEqual(
            normalize_iran_phone("09121234567"),
            "+989121234567",
        )

    def test_plus_98_number(self):
        self.assertEqual(
            normalize_iran_phone("+989121234567"),
            "+989121234567",
        )

    def test_0098_number(self):
        self.assertEqual(
            normalize_iran_phone("00989121234567"),
            "+989121234567",
        )

    def test_persian_digits(self):
        self.assertEqual(
            normalize_iran_phone("۰۹۱۲۱۲۳۴۵۶۷"),
            "+989121234567",
        )

    def test_invalid_number_raises(self):
        with self.assertRaises(InvalidPhoneNumber):
            normalize_iran_phone("12345")

    def test_landline_rejected(self):
        with self.assertRaises(InvalidPhoneNumber):
            normalize_iran_phone("02188776655")


class IranPostalCodeTests(SimpleTestCase):
    def test_valid_postal_code(self):
        self.assertEqual(
            normalize_iran_postal_code("1234567890"),
            "1234567890",
        )

    def test_persian_digits(self):
        self.assertEqual(
            normalize_iran_postal_code("۱۲۳۴۵۶۷۸۹۰"),
            "1234567890",
        )

    def test_separators_are_stripped(self):
        self.assertEqual(
            normalize_iran_postal_code("1234-5678-90"),
            "1234567890",
        )

    def test_wrong_length_rejected(self):
        for value in ("123456789", "12345678901", "12345abcde"):
            with self.subTest(value=value):
                with self.assertRaises(InvalidPostalCode):
                    normalize_iran_postal_code(value)


class WhitespaceNormalizationTests(SimpleTestCase):
    def test_collapses_whitespace_runs(self):
        self.assertEqual(
            normalize_whitespace("  علی   رضا \n محمدی\t"),
            "علی رضا محمدی",
        )

    def test_empty_string(self):
        self.assertEqual(normalize_whitespace("   "), "")
