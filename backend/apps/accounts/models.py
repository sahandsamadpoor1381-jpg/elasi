from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
    unique=True,
    null=True,
    blank=True,
)

    phone_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
    )

class PhoneOTPState(models.Model):
    phone_number = models.CharField(
        max_length=20,
        unique=True,
    )

    code_hash = models.CharField(
        max_length=255,
        blank=True,
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    resend_available_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    failed_attempts = models.PositiveSmallIntegerField(
        default=0,
    )

    request_count = models.PositiveSmallIntegerField(
        default=0,
    )

    request_window_started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    locked_until = models.DateTimeField(
        null=True,
        blank=True,
    )

    last_sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self) -> str:
        return self.phone_number

    def __str__(self) -> str:
        return self.email or self.username