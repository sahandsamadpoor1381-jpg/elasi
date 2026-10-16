from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from .sms import (
    CONSOLE_OTP_BACKEND,
    ConsoleOTPBackend,
    validate_otp_sms_backend,
)


class OTPSmsBackendGuardTests(SimpleTestCase):
    def test_console_backend_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            validate_otp_sms_backend(
                CONSOLE_OTP_BACKEND,
            )

    def test_custom_console_backend_path_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            validate_otp_sms_backend(
                "myproject.sms.OtherConsoleOTPBackend",
            )

    def test_missing_backend_is_rejected(self):
        for value in ("", "   ", None):
            with self.subTest(value=value):
                with self.assertRaises(
                    ImproperlyConfigured,
                ):
                    validate_otp_sms_backend(value)

    def test_real_provider_path_is_accepted(self):
        validate_otp_sms_backend(
            "myproject.sms.KavenegarOTPBackend",
        )

    def test_console_backend_masks_phone_number(self):
        with self.assertLogs(
            "apps.accounts.sms",
            level="WARNING",
        ) as captured:
            ConsoleOTPBackend().send_code(
                phone_number="+989121234567",
                code="123456",
            )

        message = captured.records[0].getMessage()

        self.assertIn("4567", message)

        self.assertNotIn("1234567", message)

        self.assertNotIn("+989121234567", message)

    def test_console_backend_still_emits_code_for_development(self):
        with self.assertLogs(
            "apps.accounts.sms",
            level="WARNING",
        ) as captured:
            ConsoleOTPBackend().send_code(
                phone_number="+989121234567",
                code="123456",
            )

        message = captured.records[0].getMessage()

        self.assertIn("123456", message)
