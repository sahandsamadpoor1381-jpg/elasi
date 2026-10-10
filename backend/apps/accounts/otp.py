import re
import secrets
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import (
    check_password,
    make_password,
)
from django.db import transaction
from django.utils import timezone

from .models import PhoneOTPState
from .sms import send_otp_code


User = get_user_model()


class OTPError(Exception):
    def __init__(
        self,
        code: str,
        detail: str,
        *,
        retry_after: int | None = None,
    ):
        self.code = code
        self.detail = detail
        self.retry_after = retry_after

        super().__init__(detail)


@dataclass(frozen=True)
class OTPRequestResult:
    phone_number: str
    expires_at: object
    resend_available_at: object


def normalize_iran_phone(
    value: str,
) -> str:
    digits = re.sub(
        r"\D",
        "",
        value.strip(),
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
        raise OTPError(
            "invalid_phone_number",
            "Invalid Iranian mobile number.",
        )

    return f"+98{digits}"


def generate_otp_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def seconds_until(
    target,
    *,
    now,
) -> int:
    return max(
        1,
        int(
            (
                target - now
            ).total_seconds()
        ),
    )


def request_otp(
    phone_number: str,
) -> OTPRequestResult:
    normalized_phone = (
        normalize_iran_phone(
            phone_number,
        )
    )

    now = timezone.now()

    with transaction.atomic():
        state, _ = (
            PhoneOTPState.objects.get_or_create(
                phone_number=normalized_phone,
            )
        )

        state = (
            PhoneOTPState.objects
            .select_for_update()
            .get(pk=state.pk)
        )

        if (
            state.locked_until
            and state.locked_until > now
        ):
            raise OTPError(
                "otp_locked",
                (
                    "OTP verification is "
                    "temporarily locked."
                ),
                retry_after=seconds_until(
                    state.locked_until,
                    now=now,
                ),
            )

        if (
            state.resend_available_at
            and state.resend_available_at > now
        ):
            raise OTPError(
                "resend_too_soon",
                (
                    "Please wait before "
                    "requesting another OTP."
                ),
                retry_after=seconds_until(
                    state.resend_available_at,
                    now=now,
                ),
            )

        window_seconds = (
            settings.OTP_REQUEST_WINDOW_SECONDS
        )

        window_started_at = (
            state.request_window_started_at
        )

        window_expired = (
            window_started_at is None
            or (
                now - window_started_at
            ).total_seconds()
            >= window_seconds
        )

        if window_expired:
            state.request_window_started_at = (
                now
            )
            state.request_count = 0

        if (
            state.request_count
            >= settings.OTP_MAX_REQUESTS_PER_WINDOW
        ):
            window_end = (
                state.request_window_started_at
                + timedelta(
                    seconds=window_seconds,
                )
            )

            raise OTPError(
                "request_rate_limited",
                (
                    "Too many OTP requests. "
                    "Please try again later."
                ),
                retry_after=seconds_until(
                    window_end,
                    now=now,
                ),
            )

        code = generate_otp_code()

        state.code_hash = make_password(
            code,
        )

        state.expires_at = (
            now
            + timedelta(
                seconds=(
                    settings
                    .OTP_CODE_TTL_SECONDS
                ),
            )
        )

        state.resend_available_at = (
            now
            + timedelta(
                seconds=(
                    settings
                    .OTP_RESEND_COOLDOWN_SECONDS
                ),
            )
        )

        state.failed_attempts = 0

        state.request_count += 1

        state.last_sent_at = now

        if (
            state.locked_until
            and state.locked_until <= now
        ):
            state.locked_until = None

        state.save()

    send_otp_code(
        phone_number=normalized_phone,
        code=code,
    )

    return OTPRequestResult(
        phone_number=normalized_phone,
        expires_at=state.expires_at,
        resend_available_at=(
            state.resend_available_at
        ),
    )


def verify_otp(
    *,
    phone_number: str,
    code: str,
):
    normalized_phone = normalize_iran_phone(
        phone_number,
    )

    normalized_code = code.strip()

    if not re.fullmatch(
        r"\d{6}",
        normalized_code,
    ):
        raise OTPError(
            "invalid_otp",
            "Invalid OTP code.",
        )

    now = timezone.now()

    pending_error: OTPError | None = None

    with transaction.atomic():
        try:
            state = (
                PhoneOTPState.objects
                .select_for_update()
                .get(
                    phone_number=(
                        normalized_phone
                    ),
                )
            )
        except PhoneOTPState.DoesNotExist as exc:
            raise OTPError(
                "invalid_otp",
                "Invalid OTP code.",
            ) from exc

        # Already temporarily locked.
        if (
            state.locked_until
            and state.locked_until > now
        ):
            raise OTPError(
                "otp_locked",
                (
                    "OTP verification is "
                    "temporarily locked."
                ),
                retry_after=seconds_until(
                    state.locked_until,
                    now=now,
                ),
            )

        if (
            not state.code_hash
            or not state.expires_at
        ):
            raise OTPError(
                "invalid_otp",
                "Invalid OTP code.",
            )

        # Expired OTP:
        # Persist cleanup first.
        if state.expires_at <= now:
            state.code_hash = ""
            state.expires_at = None

            state.save(
                update_fields=(
                    "code_hash",
                    "expires_at",
                    "updated_at",
                ),
            )

            pending_error = OTPError(
                "otp_expired",
                "OTP code has expired.",
            )

        # Wrong OTP:
        # Persist failed_attempts / lock before
        # raising the application-level error.
        elif not check_password(
            normalized_code,
            state.code_hash,
        ):
            state.failed_attempts += 1

            if (
                state.failed_attempts
                >= settings.OTP_MAX_VERIFY_ATTEMPTS
            ):
                state.locked_until = (
                    now
                    + timedelta(
                        seconds=(
                            settings
                            .OTP_LOCK_SECONDS
                        ),
                    )
                )

            state.save(
                update_fields=(
                    "failed_attempts",
                    "locked_until",
                    "updated_at",
                ),
            )

            if (
                state.locked_until
                and state.locked_until > now
            ):
                pending_error = OTPError(
                    "otp_locked",
                    (
                        "Too many failed "
                        "verification attempts."
                    ),
                    retry_after=seconds_until(
                        state.locked_until,
                        now=now,
                    ),
                )
            else:
                pending_error = OTPError(
                    "invalid_otp",
                    "Invalid OTP code.",
                )

        # Correct OTP.
        else:
            user = (
                User.objects.filter(
                    phone_number=(
                        normalized_phone
                    ),
                )
                .first()
            )

            if user is None:
                user = User(
                    username=normalized_phone,
                    phone_number=(
                        normalized_phone
                    ),
                    email=None,
                )

                user.set_unusable_password()

                user.save()

            # Consume OTP after successful use.
            state.code_hash = ""
            state.expires_at = None
            state.resend_available_at = None
            state.failed_attempts = 0
            state.locked_until = None
            state.request_count = 0
            state.request_window_started_at = None

            state.save(
                update_fields=(
                    "code_hash",
                    "expires_at",
                    "resend_available_at",
                    "failed_attempts",
                    "locked_until",
                    "request_count",
                    "request_window_started_at",
                    "updated_at",
                ),
            )

            return user

    # Important:
    # raise AFTER transaction.atomic() exits,
    # so database changes are committed.
    if pending_error is not None:
        raise pending_error

    raise OTPError(
        "invalid_otp",
        "Invalid OTP code.",
    )