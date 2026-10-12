import logging

from django.conf import settings
from django.utils.module_loading import import_string


logger = logging.getLogger(__name__)


class BaseOTPBackend:
    def send_code(
        self,
        *,
        phone_number: str,
        code: str,
    ) -> None:
        raise NotImplementedError


class ConsoleOTPBackend(BaseOTPBackend):
    def send_code(
        self,
        *,
        phone_number: str,
        code: str,
    ) -> None:
        logger.warning(
            "DEVELOPMENT OTP for %s: %s",
            phone_number,
            code,
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