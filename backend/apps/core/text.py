"""
Persian/Arabic text normalization for customer search.

The storefront is Persian, and shoppers type with a mix of Persian and
Arabic letter forms, Persian/Arabic/Latin digits, half-spaces (ZWNJ) and
inconsistent whitespace. Searching raw ``icontains`` against such input
silently returns nothing ("انگشتر طلا" vs "انگشتر‏طلا", "ي" vs "ی").

Both sides of a comparison are normalized with :func:`normalize_fa`:
catalog rows store a normalized ``search_text`` and the incoming query
is normalized the same way, so the lookup stays a plain, parameterized
``icontains`` (no raw SQL, no injection surface).
"""

from __future__ import annotations

import re
import unicodedata

# Letter forms that must compare equal.
LETTER_EQUIVALENCES = {
    "\u064a": "\u06cc",  # ARABIC LETTER YEH -> PERSIAN YEH  (ي -> ی)
    "\u0649": "\u06cc",  # ARABIC LETTER ALEF MAKSURA -> PERSIAN YEH
    "\u0643": "\u06a9",  # ARABIC LETTER KAF -> PERSIAN KAF  (ك -> ک)
    "\u0623": "\u0627",  # ALEF WITH HAMZA ABOVE -> ALEF
    "\u0625": "\u0627",  # ALEF WITH HAMZA BELOW -> ALEF
    "\u0622": "\u0627",  # ALEF WITH MADDA ABOVE -> ALEF
    "\u0671": "\u0627",  # ALEF WASLA -> ALEF
    "\u06c0": "\u0647",  # HEH WITH YEH MARK -> HEH  (ۀ -> ه)
    "\u06d5": "\u0647",  # AE -> HEH
    "\u0643": "\u06a9",
}

# Kashida/tatweel carries no meaning and breaks matching.
TATWEEL = "\u0640"

# Half-space (ZWNJ) and zero-width joiner: treated as a word boundary
# so "نیم‌ست" also matches "نیم ست".
ZERO_WIDTH = ("\u200c", "\u200d", "\u200e", "\u200f", "\ufeff")

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
ASCII_DIGITS = "0123456789"

DIGIT_TRANSLATION = str.maketrans(
    PERSIAN_DIGITS + ARABIC_DIGITS,
    ASCII_DIGITS + ASCII_DIGITS,
)

LETTER_TRANSLATION = str.maketrans(LETTER_EQUIVALENCES)

WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize_fa(value: object) -> str:
    """Return a search-comparable form of ``value``.

    Deterministic and side-effect free; safe for both stored text and
    user input.
    """

    if value is None:
        return ""

    text = unicodedata.normalize("NFKC", str(value))

    text = text.replace(TATWEEL, "")

    for character in ZERO_WIDTH:
        text = text.replace(character, " ")

    text = text.translate(DIGIT_TRANSLATION)
    text = text.translate(LETTER_TRANSLATION)

    # Latin input is case-insensitive; Persian has no case.
    text = text.lower()

    return WHITESPACE_PATTERN.sub(" ", text).strip()


def normalize_search_query(value: object) -> str:
    """Normalize a customer query and collapse it to searchable terms."""

    return normalize_fa(value)


def search_terms(value: object) -> list[str]:
    """Split a normalized query into individual terms (AND semantics)."""

    normalized = normalize_fa(value)

    if not normalized:
        return []

    return [term for term in normalized.split(" ") if term]
