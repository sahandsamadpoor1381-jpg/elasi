"""
Shared input-validation helpers for ELASI.

These helpers are the single authoritative implementation of:

- Persian / Arabic / Latin digit normalization
- Iranian mobile-number normalization
- Iranian postal-code normalization
- whitespace normalization for human-entered text

``apps.accounts.otp`` re-exports the digit and phone helpers so the OTP
module keeps its historical import surface, while other apps (for
example checkout validation) can depend on this neutral module instead
of reaching into the accounts OTP internals.
"""

import re


PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
ASCII_DIGITS = "0123456789"

DIGIT_TRANSLATION = str.maketrans(
    PERSIAN_DIGITS + ARABIC_DIGITS,
    ASCII_DIGITS + ASCII_DIGITS,
)


class InvalidPhoneNumber(ValueError):
    """Raised when a value is not a supported Iranian mobile number."""


class InvalidPostalCode(ValueError):
    """Raised when a value is not a valid Iranian postal code."""


def normalize_digits(value: str) -> str:
    """
    Convert Persian and Arabic digits to ASCII digits.

    Examples:
        ۰۹۱۲۱۲۳۴۵۶۷ -> 09121234567
        ٠٩١٢١٢٣٤٥٦٧ -> 09121234567
        ۱۲۳۴۵۶       -> 123456
    """

    return value.translate(
        DIGIT_TRANSLATION,
    )


def normalize_iran_phone(value: str) -> str:
    """
    Normalize supported Iranian mobile number formats to
    E.164-style ``+98`` format.

    Accepted inputs include ``09121234567``, ``+989121234567``,
    ``00989121234567`` and Persian-digit spellings of those forms.

    Raises ``InvalidPhoneNumber`` for anything else.
    """

    digits = re.sub(
        r"\D",
        "",
        normalize_digits(
            value.strip(),
        ),
    )

    if digits.startswith("0098"):
        digits = digits[4:]

    elif digits.startswith("98"):
        digits = digits[2:]

    elif digits.startswith("0"):
        digits = digits[1:]

    if not re.fullmatch(
        r"9\d{9}",
        digits,
    ):
        raise InvalidPhoneNumber(
            "Invalid Iranian mobile number.",
        )

    return f"+98{digits}"


def normalize_iran_postal_code(value: str) -> str:
    """
    Normalize an Iranian postal code to exactly ten ASCII digits.

    Persian and Arabic digits are accepted and converted.

    Raises ``InvalidPostalCode`` for anything that is not ten digits.
    """

    digits = re.sub(
        r"\D",
        "",
        normalize_digits(
            value.strip(),
        ),
    )

    if not re.fullmatch(
        r"\d{10}",
        digits,
    ):
        raise InvalidPostalCode(
            "Iranian postal code must be exactly 10 digits.",
        )

    return digits


def normalize_whitespace(value: str) -> str:
    """
    Collapse all whitespace runs (including newlines and tabs) into
    single spaces and strip the ends.

    Used for names and short human-entered text so stored data never
    contains padded, multiline or otherwise malformed values.
    """

    return re.sub(
        r"\s+",
        " ",
        value,
    ).strip()
