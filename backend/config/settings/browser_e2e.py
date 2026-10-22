"""Isolated, loopback-only browser integration test settings.

ONLY for ``manage.py testserver`` with synthetic fixtures. Never use this
settings module for development databases, staging or production.
"""

import os

from django.core.exceptions import ImproperlyConfigured

if os.environ.get("ELASI_BROWSER_E2E_TESTING") != "1":
    raise ImproperlyConfigured(
        "Browser E2E settings require ELASI_BROWSER_E2E_TESTING=1."
    )

if not os.environ.get("ELASI_E2E_OTP_FILE"):
    raise ImproperlyConfigured("ELASI_E2E_OTP_FILE is required.")

# Always use an isolated in-memory SQLite database, even if the developer
# normally runs PostgreSQL-backed concurrency tests.
os.environ["ELASI_TEST_USE_POSTGRES"] = "0"

from .test import *  # noqa: E402,F403

# A fake delivery backend is only available within this test settings module.
OTP_SMS_BACKEND = "apps.accounts.browser_e2e_sms.BrowserE2EOTPBackend"
ELASI_E2E_OTP_FILE = os.environ["ELASI_E2E_OTP_FILE"]

# Synthetic test tariff; NOT the real merchant's shipping policy.
ELASI_POSTAL_SHIPPING_FEE_RIAL = 150000

CSRF_TRUSTED_ORIGINS = [
    *CSRF_TRUSTED_ORIGINS,  # noqa: F405
    "http://127.0.0.1:3110",
]

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
