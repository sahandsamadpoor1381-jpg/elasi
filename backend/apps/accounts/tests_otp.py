from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import (
    get_user_model,
)
from django.contrib.auth.hashers import (
    check_password,
)
from django.test import TestCase
from django.utils import timezone

from .models import PhoneOTPState
from .otp import (
    OTPError,
    normalize_iran_phone,
    request_otp,
    verify_otp,
)


User = get_user_model()


class PhoneNormalizationTests(
    TestCase,
):
    def test_normalizes_local_iran_number(
        self,
    ):
        self.assertEqual(
            normalize_iran_phone(
                "09121234567",
            ),
            "+989121234567",
        )

    def test_normalizes_international_iran_number(
        self,
    ):
        self.assertEqual(
            normalize_iran_phone(
                "+98 912 123 4567",
            ),
            "+989121234567",
        )

    def test_normalizes_persian_digits(
        self,
    ):
        self.assertEqual(
            normalize_iran_phone(
                "۰۹۱۲۱۲۳۴۵۶۷",
            ),
            "+989121234567",
        )

    def test_rejects_invalid_phone_number(
        self,
    ):
        with self.assertRaises(
            OTPError,
        ):
            normalize_iran_phone(
                "12345",
            )


class OTPServiceTests(TestCase):
    @patch(
        "apps.accounts.otp.generate_otp_code",
        return_value="123456",
    )
    @patch(
        "apps.accounts.otp.send_otp_code",
    )
    def test_request_stores_hash_not_plain_code(
        self,
        send_mock,
        generate_mock,
    ):
        result = request_otp(
            "09121234567",
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

        self.assertEqual(
            result.phone_number,
            "+989121234567",
        )

        send_mock.assert_called_once_with(
            phone_number=(
                "+989121234567"
            ),
            code="123456",
        )

    @patch(
        "apps.accounts.otp.generate_otp_code",
        return_value="123456",
    )
    @patch(
        "apps.accounts.otp.send_otp_code",
    )
    def test_resend_cooldown_is_enforced(
        self,
        send_mock,
        generate_mock,
    ):
        request_otp(
            "09121234567",
        )

        with self.assertRaises(
            OTPError,
        ) as context:
            request_otp(
                "09121234567",
            )

        self.assertEqual(
            context.exception.code,
            "resend_too_soon",
        )

        self.assertIsNotNone(
            context.exception.retry_after,
        )

    @patch(
        "apps.accounts.otp.generate_otp_code",
        return_value="123456",
    )
    @patch(
        "apps.accounts.otp.send_otp_code",
    )
    def test_valid_otp_creates_user(
        self,
        send_mock,
        generate_mock,
    ):
        request_otp(
            "09121234567",
        )

        user = verify_otp(
            phone_number=(
                "09121234567"
            ),
            code="123456",
        )

        self.assertEqual(
            user.phone_number,
            "+989121234567",
        )

        self.assertIsNone(
            user.email,
        )

        self.assertFalse(
            user.has_usable_password(),
        )

        self.assertEqual(
            User.objects.count(),
            1,
        )

    @patch(
        "apps.accounts.otp.generate_otp_code",
        return_value="123456",
    )
    @patch(
        "apps.accounts.otp.send_otp_code",
    )
    def test_accepts_persian_digits_for_otp(
        self,
        send_mock,
        generate_mock,
    ):
        request_otp(
            "۰۹۱۲۱۲۳۴۵۶۷",
        )

        user = verify_otp(
            phone_number=(
                "۰۹۱۲۱۲۳۴۵۶۷"
            ),
            code="۱۲۳۴۵۶",
        )

        self.assertEqual(
            user.phone_number,
            "+989121234567",
        )

    @patch(
        "apps.accounts.otp.generate_otp_code",
        return_value="123456",
    )
    @patch(
        "apps.accounts.otp.send_otp_code",
    )
    def test_valid_otp_is_consumed(
        self,
        send_mock,
        generate_mock,
    ):
        request_otp(
            "09121234567",
        )

        verify_otp(
            phone_number=(
                "09121234567"
            ),
            code="123456",
        )

        with self.assertRaises(
            OTPError,
        ):
            verify_otp(
                phone_number=(
                    "09121234567"
                ),
                code="123456",
            )

    @patch(
        "apps.accounts.otp.generate_otp_code",
        return_value="123456",
    )
    @patch(
        "apps.accounts.otp.send_otp_code",
    )
    def test_wrong_code_increments_attempts(
        self,
        send_mock,
        generate_mock,
    ):
        request_otp(
            "09121234567",
        )

        with self.assertRaises(
            OTPError,
        ) as context:
            verify_otp(
                phone_number=(
                    "09121234567"
                ),
                code="654321",
            )

        self.assertEqual(
            context.exception.code,
            "invalid_otp",
        )

        state = (
            PhoneOTPState.objects.get(
                phone_number=(
                    "+989121234567"
                ),
            )
        )

        self.assertEqual(
            state.failed_attempts,
            1,
        )

    @patch(
        "apps.accounts.otp.generate_otp_code",
        return_value="123456",
    )
    @patch(
        "apps.accounts.otp.send_otp_code",
    )
    def test_expired_code_is_rejected(
        self,
        send_mock,
        generate_mock,
    ):
        request_otp(
            "09121234567",
        )

        state = (
            PhoneOTPState.objects.get(
                phone_number=(
                    "+989121234567"
                ),
            )
        )

        state.expires_at = (
            timezone.now()
            - timedelta(seconds=1)
        )

        state.save(
            update_fields=(
                "expires_at",
            ),
        )

        with self.assertRaises(
            OTPError,
        ) as context:
            verify_otp(
                phone_number=(
                    "09121234567"
                ),
                code="123456",
            )

        self.assertEqual(
            context.exception.code,
            "otp_expired",
        )

        state.refresh_from_db()

        self.assertEqual(
            state.code_hash,
            "",
        )

        self.assertIsNone(
            state.expires_at,
        )

    @patch(
        "apps.accounts.otp.generate_otp_code",
        return_value="123456",
    )
    @patch(
        "apps.accounts.otp.send_otp_code",
    )
    def test_wrong_attempts_eventually_lock_otp(
        self,
        send_mock,
        generate_mock,
    ):
        request_otp(
            "09121234567",
        )

        max_attempts = 5

        for attempt in range(
            max_attempts,
        ):
            with self.assertRaises(
                OTPError,
            ) as context:
                verify_otp(
                    phone_number=(
                        "09121234567"
                    ),
                    code="654321",
                )

            if (
                attempt
                < max_attempts - 1
            ):
                self.assertEqual(
                    context.exception.code,
                    "invalid_otp",
                )

        self.assertEqual(
            context.exception.code,
            "otp_locked",
        )

        state = (
            PhoneOTPState.objects.get(
                phone_number=(
                    "+989121234567"
                ),
            )
        )

        self.assertEqual(
            state.failed_attempts,
            max_attempts,
        )

        self.assertIsNotNone(
            state.locked_until,
        )

        self.assertGreater(
            state.locked_until,
            timezone.now(),
        )

    @patch(
        "apps.accounts.otp.generate_otp_code",
        return_value="123456",
    )
    @patch(
        "apps.accounts.otp.send_otp_code",
    )
    def test_successful_verification_resets_otp_state(
        self,
        send_mock,
        generate_mock,
    ):
        request_otp(
            "09121234567",
        )

        with self.assertRaises(
            OTPError,
        ):
            verify_otp(
                phone_number=(
                    "09121234567"
                ),
                code="654321",
            )

        user = verify_otp(
            phone_number=(
                "09121234567"
            ),
            code="123456",
        )

        self.assertEqual(
            user.phone_number,
            "+989121234567",
        )

        state = (
            PhoneOTPState.objects.get(
                phone_number=(
                    "+989121234567"
                ),
            )
        )

        self.assertEqual(
            state.code_hash,
            "",
        )

        self.assertIsNone(
            state.expires_at,
        )

        self.assertIsNone(
            state.resend_available_at,
        )

        self.assertEqual(
            state.failed_attempts,
            0,
        )

        self.assertIsNone(
            state.locked_until,
        )

        self.assertEqual(
            state.request_count,
            0,
        )

        self.assertIsNone(
            state.request_window_started_at,
        )