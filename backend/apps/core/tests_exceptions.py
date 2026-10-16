"""
Contract tests for the shared DRF exception handler
(``apps.core.exceptions.elasi_exception_handler``).

The handler exists so storefront clients can react to CSRF and session
rejections through a stable machine-readable ``code`` instead of parsing
English framework prose - which used to be shown to customers verbatim
("CSRF Failed: CSRF cookie not set.").

These tests pin two things at once:
  * CSRF protection is still fully enforced (nothing is exempted, a
    missing cookie or a wrong token is still rejected with 403);
  * the response contract stays backwards compatible (status codes and
    DRF's ``detail`` text are unchanged; ``code`` is only added, and an
    application-level ``code`` is never overwritten).
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()

CSRF_URL = "/api/v1/auth/csrf/"
OTP_REQUEST_URL = "/api/v1/auth/otp/request/"
SESSION_URL = "/api/v1/auth/session/"

VALID_PHONE = "09120000000"


class CsrfCookieIssuanceTests(TestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

    def test_csrf_endpoint_sets_a_readable_cookie(self):
        response = self.client.get(
            CSRF_URL,
            HTTP_ORIGIN="http://localhost:3000",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("csrf_token", response.json())

        cookie = response.cookies.get("csrftoken")
        self.assertIsNotNone(cookie)

        # The storefront must be able to read the token, and the cookie
        # must survive the SameSite=Lax first-party topology.
        self.assertFalse(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertEqual(cookie["path"], "/")

        # Development runs over plain HTTP: a Secure flag would make the
        # browser discard the cookie entirely.
        self.assertFalse(cookie["secure"])


class CsrfEnforcementContractTests(TestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

    def test_missing_cookie_is_rejected_with_stable_code(self):
        response = self.client.post(
            OTP_REQUEST_URL,
            {"phone_number": VALID_PHONE},
            format="json",
            HTTP_ORIGIN="http://localhost:3000",
        )

        self.assertEqual(response.status_code, 403)

        payload = response.json()
        self.assertEqual(payload["code"], "csrf_failed")

        # DRF's own text is preserved for existing clients.
        self.assertTrue(
            payload["detail"].startswith("CSRF Failed"),
        )

    def test_wrong_token_is_rejected_with_stable_code(self):
        self.client.get(
            CSRF_URL,
            HTTP_ORIGIN="http://localhost:3000",
        )

        response = self.client.post(
            OTP_REQUEST_URL,
            {"phone_number": VALID_PHONE},
            format="json",
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_X_CSRFTOKEN="not-a-real-token",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["code"],
            "csrf_failed",
        )

    def test_valid_token_is_accepted(self):
        csrf_response = self.client.get(
            CSRF_URL,
            HTTP_ORIGIN="http://localhost:3000",
        )

        token = csrf_response.json()["csrf_token"]

        response = self.client.post(
            OTP_REQUEST_URL,
            {"phone_number": VALID_PHONE},
            format="json",
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, 200)


class SessionRejectionContractTests(TestCase):
    def test_anonymous_session_read_is_coded(self):
        client = APIClient(enforce_csrf_checks=True)

        response = client.get(
            SESSION_URL,
            HTTP_ORIGIN="http://localhost:3000",
        )

        self.assertEqual(response.status_code, 403)

        payload = response.json()
        self.assertEqual(payload["code"], "not_authenticated")
        self.assertEqual(
            payload["detail"],
            "Authentication credentials were not provided.",
        )


class ApplicationCodePrecedenceTests(TestCase):
    """An application-level ``code`` must never be overwritten."""

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.user = User.objects.create_user(
            username="exc-code",
            email="exc-code@example.com",
            phone_number="+989120000000",
            password="test-password",
        )

    def test_business_error_code_is_preserved(self):
        csrf_response = self.client.get(
            CSRF_URL,
            HTTP_ORIGIN="http://localhost:3000",
        )
        token = csrf_response.json()["csrf_token"]

        # An invalid phone number is a business rejection that already
        # carries its own code and must be left untouched.
        response = self.client.post(
            OTP_REQUEST_URL,
            {"phone_number": "123"},
            format="json",
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, 400)

        payload = response.json()
        self.assertEqual(
            payload["code"],
            "invalid_phone_number",
        )
