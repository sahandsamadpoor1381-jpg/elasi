import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string


logger = logging.getLogger(__name__)


CONSOLE_OTP_BACKEND = (
    "apps.accounts.sms.ConsoleOTPBackend"
)


class BaseOTPBackend:
    def send_code(
        self,
        *,
        phone_number: str,
        code: str,
    ) -> None:
        raise NotImplementedError


class ConsoleOTPBackend(BaseOTPBackend):
    """
    Development-only backend that writes the OTP code to the
    process log.

    This backend must never run in production: the log message
    intentionally contains the one-time code. Production settings
    call ``validate_otp_sms_backend()`` to reject it at startup.
    """

    def send_code(
        self,
        *,
        phone_number: str,
        code: str,
    ) -> None:
        logger.warning(
            "DEVELOPMENT OTP for number ending %s: %s",
            phone_number[-4:],
            code,
        )


def validate_otp_sms_backend(
    backend_path: str,
) -> None:
    """
    Fail fast when OTP delivery is not backed by a real SMS
    provider.

    ``backend_path`` must be a non-empty dotted path that is not
    the development ``ConsoleOTPBackend``. Raises
    ``ImproperlyConfigured`` otherwise.

    This function is deliberately pure (it does not read settings)
    so that production settings can validate the raw environment
    value at import time and unit tests can cover it directly.
    """

    normalized = (backend_path or "").strip()

    if not normalized:
        raise ImproperlyConfigured(
            "OTP_SMS_BACKEND is not configured. Production "
            "requires a real SMS provider backend."
        )

    if normalized == CONSOLE_OTP_BACKEND or normalized.endswith(
        "ConsoleOTPBackend"
    ):
        raise ImproperlyConfigured(
            "OTP_SMS_BACKEND points at the development "
            "ConsoleOTPBackend, which writes OTP codes to the "
            "process log. Production requires a real SMS "
            "provider backend."
        )


def get_otp_backend() -> BaseOTPBackend:
    backend_class = import_string(
        settings.OTP_SMS_BACKEND,
    )

    return backend_class()


def send_otp_code(
    *,
    phone_number: str,
    code: str,
) -> None:
    get_otp_backend().send_code(
        phone_number=phone_number,
        code=code,
    )
