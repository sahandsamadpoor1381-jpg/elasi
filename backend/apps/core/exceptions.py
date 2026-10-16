"""
Shared DRF exception handling.

DRF reports CSRF and session rejections only through human-readable
English text (``"CSRF Failed: CSRF cookie not set."``), which forces
API clients to pattern-match prose - and which used to be surfaced
verbatim to customers by the storefront.

This handler adds a stable, machine-readable ``code`` to those
rejections so clients can react precisely:

``csrf_failed``
    The request was rejected by Django's CSRF protection. The client
    must obtain a fresh CSRF token (Django rotates the secret on
    login) and may retry exactly once.
``not_authenticated``
    No valid session; the client should send the customer to sign in.
``permission_denied``
    Authenticated but not allowed.

Nothing here weakens CSRF or session enforcement: the response status
and DRF's ``detail`` text are preserved, and existing clients that only
read ``detail`` keep working. Customer-facing Persian copy stays in the
frontend so the API contract remains language-neutral.
"""

from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.exceptions import (
    NotAuthenticated,
    PermissionDenied,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler

CSRF_DETAIL_PREFIX = "CSRF Failed"


def resolve_error_code(
    exc: Any,
    response: Response,
) -> str | None:
    """Map a DRF exception to a stable client-facing code."""

    if isinstance(exc, PermissionDenied):
        detail = exc.detail

        if isinstance(detail, str) and detail.startswith(
            CSRF_DETAIL_PREFIX,
        ):
            return "csrf_failed"

        return "permission_denied"

    if isinstance(exc, NotAuthenticated):
        return "not_authenticated"

    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        return "not_authenticated"

    if response.status_code == status.HTTP_403_FORBIDDEN:
        return "permission_denied"

    return None


def elasi_exception_handler(
    exc: Any,
    context: dict[str, Any],
) -> Response | None:
    response = exception_handler(exc, context)

    if response is None:
        return response

    # Only object payloads can carry a code; list payloads (some
    # ValidationError shapes) are left untouched.
    if not isinstance(response.data, dict):
        return response

    if "code" in response.data:
        return response

    code = resolve_error_code(exc, response)

    if code is not None:
        response.data["code"] = code

    return response
