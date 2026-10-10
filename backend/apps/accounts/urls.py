from django.urls import path

from .auth_views import (
    CSRFTokenAPIView,
    LogoutAPIView,
    OTPRequestAPIView,
    OTPVerifyAPIView,
    SessionAPIView,
)


app_name = "accounts"


urlpatterns = [
    path(
        "csrf/",
        CSRFTokenAPIView.as_view(),
        name="csrf",
    ),
    path(
        "otp/request/",
        OTPRequestAPIView.as_view(),
        name="otp-request",
    ),
    path(
        "otp/verify/",
        OTPVerifyAPIView.as_view(),
        name="otp-verify",
    ),
    path(
        "session/",
        SessionAPIView.as_view(),
        name="session",
    ),
    path(
        "logout/",
        LogoutAPIView.as_view(),
        name="logout",
    ),
]