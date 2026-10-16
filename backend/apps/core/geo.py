"""
Iran province/city reference data for server-side address
validation.

The dataset is derived from the same source the storefront uses
(``frontend/src/data/iran``) so that client-side selection and
server-side validation accept exactly the same values. Checkout
sends province and city as Persian display names; this module is
the backend authority for their compatibility.

Loaded once at import time and kept in memory (the dataset is a
few tens of kilobytes).
"""

import json
from functools import lru_cache
from pathlib import Path


DATA_FILE = (
    Path(__file__).resolve().parent
    / "data"
    / "iran_geo.json"
)


class InvalidAddress(ValueError):
    """
    Raised when province/city values are unknown or incompatible.

    ``field`` names the offending input (``"province"`` or ``"city"``)
    so API layers can attach the error to the right form field.
    """

    def __init__(
        self,
        message: str,
        *,
        field: str = "city",
    ):
        super().__init__(message)
        self.field = field


@lru_cache(maxsize=1)
def load_iran_geo() -> dict:
    with DATA_FILE.open(
        encoding="utf-8",
    ) as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def _province_index() -> dict:
    index = {}

    for province in load_iran_geo()["provinces"]:
        index[province["name"]] = {
            "id": province["id"],
            "cities": frozenset(province["cities"]),
        }

    return index


def normalize_address_name(value: str) -> str:
    """
    Normalize a Persian province/city name for lookup: trim the
    ends and collapse internal whitespace.
    """

    from .validators import normalize_whitespace

    return normalize_whitespace(value or "")


def validate_iran_province_city(
    province: str,
    city: str,
) -> tuple[str, str]:
    """
    Validate that ``province`` is a known Iranian province and
    that ``city`` belongs to it.

    Returns the normalized ``(province, city)`` pair on success.

    Raises ``InvalidAddress`` for unknown provinces, unknown
    cities or an incompatible province/city combination.
    """

    normalized_province = normalize_address_name(province)
    normalized_city = normalize_address_name(city)

    if not normalized_province:
        raise InvalidAddress(
            "Province is required.",
            field="province",
        )

    if not normalized_city:
        raise InvalidAddress(
            "City is required.",
            field="city",
        )

    province_entry = _province_index().get(
        normalized_province,
    )

    if province_entry is None:
        raise InvalidAddress(
            "Unknown province.",
            field="province",
        )

    if normalized_city not in province_entry["cities"]:
        raise InvalidAddress(
            "City does not belong to the selected province.",
            field="city",
        )

    return normalized_province, normalized_city
