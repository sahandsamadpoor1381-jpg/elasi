"""Capture local-browser-test OTP without an external SMS provider.

Imported only by config.settings.browser_e2e. This code must never be
configured as a production or regular-development OTP backend.
"""

import json
import os
from pathlib import Path

from django.conf import settings

from .sms import BaseOTPBackend


class BrowserE2EOTPBackend(BaseOTPBackend):
    def send_code(self, *, phone_number: str, code: str) -> None:
        if (
            settings.SETTINGS_MODULE != "config.settings.browser_e2e"
            or os.environ.get("ELASI_BROWSER_E2E_TESTING") != "1"
        ):
            raise RuntimeError("Browser test OTP backend is test-only.")

        # Owner-readable temporary file; never sent via an HTTP endpoint.
        path = Path(settings.ELASI_E2E_OTP_FILE)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump({"phone_number": phone_number, "code": code}, handle)
