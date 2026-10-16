from .base import *  # noqa: F403

from django.core.exceptions import ImproperlyConfigured

from apps.accounts.sms import validate_otp_sms_backend


DEBUG = False

# Fail fast when OTP delivery would fall back to the development
# console backend: production OTP codes must go through a real SMS
# provider and must never be written to process logs.
#
# ``env`` comes from base.py's django-environ configuration. The raw
# environment value is validated here (instead of settings.OTP_SMS_BACKEND)
# because settings modules cannot safely access the settings object
# while they are still being imported.
_otp_sms_backend = env("OTP_SMS_BACKEND", default="")  # noqa: F405

validate_otp_sms_backend(_otp_sms_backend)
