"""
Test settings for the ELASI backend.

Usage:
    python manage.py test --settings=config.settings.test

Database selection:
- Default: in-memory SQLite. This is portable and runs the full unit and
  API suite. On SQLite, ``select_for_update()`` is a silent no-op, so
  true row-locking concurrency tests are skipped automatically via
  ``connection.features.has_select_for_update``.
- Set ``ELASI_TEST_USE_POSTGRES=1`` (plus the usual ``DB_*`` variables)
  to run the same suite against a real PostgreSQL server. Concurrency
  tests are executed only in that mode.

These settings must never be used outside automated tests.
"""

import os

# Required environment defaults so that ``base`` can import without a
# real ``.env`` file. Values are test-only placeholders.
os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-secret-key")
os.environ.setdefault("DJANGO_DEBUG", "false")
os.environ.setdefault(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1,testserver",
)
os.environ.setdefault(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000",
)
os.environ.setdefault(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)
os.environ.setdefault("DB_NAME", "elasi")
os.environ.setdefault("DB_USER", "elasi")
os.environ.setdefault("DB_PASSWORD", "test-only")
os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("DB_PORT", "5432")

from .base import *  # noqa: E402,F403

DEBUG = False

# Existing checkout tests explicitly use the approved-for-tests free policy;
# no default zero fee is implied for development or production deployments.
ELASI_POSTAL_SHIPPING_FEE_RIAL = 0

USE_POSTGRES = (
    os.environ.get("ELASI_TEST_USE_POSTGRES", "").lower()
    in {"1", "true", "yes"}
)

if not USE_POSTGRES:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

# Keep hashing fast and deterministic in tests only.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
