from unittest.mock import patch

from django.contrib.auth import (
    get_user_model,
)
from django.contrib.auth.hashers import (
    check_password,
)

from rest_framework import status
from rest_framework.test import (
    APIClient,
    APITestCase,
)

from .models import PhoneOTPState
from .otp import request_otp


User = get_user_model()


class AuthAPITests(APITestCase):
    def get_csrf_token(
        self,
        client=None,
    ) -> str:
        active_client = (
            client or self.client
        )

        response = active_client.get(
            "/api/v1/auth/csrf/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        return response.json()[
            "csrf_token"
        ]

    def test_session_requires_authentication(
        self,
    ):
        response = self.client.get(
            "/api/v1/auth/session/",
        )

        self.assertIn(
            response.status_code,
            (
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ),
        )

    def test_csrf_endpoint_returns_token(
        self,
    ):
        response = self.client.get(
            "/api/v1/auth/csrf/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            response.json()[
                "csrf_token"
            ],
        )

    @patch(
        "apps.accounts.otp.generate_otp_code",
        return_value="123456",
    )
    @patch(
        "apps.accounts.otp.send_otp_code",
    )
    def test_otp_request_does_not_expose_code(
        self,
        send_mock,
        generate_mock,
    ):
        csrf_token = (
            self.get_csrf_token()
        )

        response = self.client.post(
            "/api/v1/auth/otp/request/",
            {
                "phone_number": (
                    "09121234567"
                ),
            },
            format="json",
            HTTP_X_CSRFTOKEN=(
                csrf_token
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        payload = response.json()

        self.assertNotIn(
            "code",
            payload,
        )

        state = (
            PhoneOTPState.objects.get(
                phone_number=(
                    "+989121234567"
                ),
            )
        )

        self.assertNotEqual(
            state.code_hash,
            "123456",
        )

        self.assertTrue(
            check_password(
                "123456",
                state.code_hash,
            )
        )

    @patch(
        "apps.accounts.otp.generate_otp_code",
        return_value="123456",
    )
    @patch(
        "apps.accounts.otp.send_otp_code",
    )
    def test_verify_creates_authenticated_session(
        self,
        send_mock,
        generate_mock,
    ):
        csrf_token = (
            self.get_csrf_token()
        )

        request_otp(
            "09121234567",
        )

        response = self.client.post(
            "/api/v1/auth/otp/verify/",
            {
                "phone_number": (
                    "09121234567"
                ),
                "code": "123456",
            },
            format="json",
            HTTP_X_CSRFTOKEN=(
                csrf_token
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            response.json()[
                "authenticated"
            ],
        )

        session_response = (
            self.client.get(
                "/api/v1/auth/session/",
            )
        )

        self.assertEqual(
            session_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            session_response.json()[
                "user"
            ][
                "phone_number"
            ],
            "+989121234567",
        )

    @patch(
        "apps.accounts.otp.generate_otp_code",
        return_value="123456",
    )
    @patch(
        "apps.accounts.otp.send_otp_code",
    )
    def test_wrong_otp_does_not_login_user(
        self,
        send_mock,
        generate_mock,
    ):
        csrf_token = (
            self.get_csrf_token()
        )

        request_otp(
            "09121234567",
        )

        response = self.client.post(
            "/api/v1/auth/otp/verify/",
            {
                "phone_number": (
                    "09121234567"
                ),
                "code": "654321",
            },
            format="json",
            HTTP_X_CSRFTOKEN=(
                csrf_token
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        session_response = (
            self.client.get(
                "/api/v1/auth/session/",
            )
        )

        self.assertIn(
            session_response.status_code,
            (
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ),
        )

    @patch(
        "apps.accounts.otp.generate_otp_code",
        return_value="123456",
    )
    @patch(
        "apps.accounts.otp.send_otp_code",
    )
    def test_logout_ends_session(
        self,
        send_mock,
        generate_mock,
    ):
        csrf_token = (
            self.get_csrf_token()
        )

        request_otp(
            "09121234567",
        )

        verify_response = (
            self.client.post(
                "/api/v1/auth/otp/verify/",
                {
                    "phone_number": (
                        "09121234567"
                    ),
                    "code": "123456",
                },
                format="json",
                HTTP_X_CSRFTOKEN=(
                    csrf_token
                ),
            )
        )

        self.assertEqual(
            verify_response.status_code,
            status.HTTP_200_OK,
        )

        logout_response = (
            self.client.post(
                "/api/v1/auth/logout/",
                {},
                format="json",
                HTTP_X_CSRFTOKEN=(
                    csrf_token
                ),
            )
        )

        self.assertEqual(
            logout_response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        session_response = (
            self.client.get(
                "/api/v1/auth/session/",
            )
        )

        self.assertIn(
            session_response.status_code,
            (
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ),
        )

    def test_otp_request_requires_csrf(
        self,
    ):
        csrf_client = APIClient(
            enforce_csrf_checks=True,
        )

        response = csrf_client.post(
            "/api/v1/auth/otp/request/",
            {
                "phone_number": (
                    "09121234567"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )