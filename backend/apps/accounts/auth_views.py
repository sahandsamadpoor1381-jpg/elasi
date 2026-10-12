from django.conf import settings
from django.contrib.auth import (
    login as django_login,
    logout as django_logout,
)
from django.middleware.csrf import get_token

from rest_framework import status
from rest_framework.authentication import (
    SessionAuthentication,
)
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth_serializers import (
    CurrentUserSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
)
from .otp import (
    OTPError,
    request_otp,
    verify_otp,
)


def enforce_csrf(
    request: Request,
) -> None:
    """
    Explicit CSRF validation for anonymous POST
    endpoints such as OTP request and verify.

    DRF's normal SessionAuthentication only
    enforces CSRF after a session-authenticated
    user exists, so login endpoints need an
    explicit check.
    """

    SessionAuthentication().enforce_csrf(
        request,
    )


def otp_error_response(
    error: OTPError,
) -> Response:
    payload: dict[str, object] = {
        "code": error.code,
        "detail": error.detail,
    }

    if error.retry_after is not None:
        payload["retry_after"] = (
            error.retry_after
        )

    if error.code in {
        "resend_too_soon",
        "request_rate_limited",
        "otp_locked",
    }:
        response_status = (
            status.HTTP_429_TOO_MANY_REQUESTS
        )

    elif error.code == "account_disabled":
        response_status = (
            status.HTTP_403_FORBIDDEN
        )

    else:
        response_status = (
            status.HTTP_400_BAD_REQUEST
        )

    return Response(
        payload,
        status=response_status,
    )


class CSRFTokenAPIView(APIView):
    permission_classes = (
        AllowAny,
    )

    authentication_classes = ()

    def get(
        self,
        request: Request,
    ) -> Response:
        csrf_token = get_token(
            request,
        )

        return Response(
            {
                "csrf_token": csrf_token,
            },
        )


class OTPRequestAPIView(APIView):
    permission_classes = (
        AllowAny,
    )

    authentication_classes = ()

    def post(
        self,
        request: Request,
    ) -> Response:
        enforce_csrf(request)

        serializer = (
            OTPRequestSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            result = request_otp(
                serializer.validated_data[
                    "phone_number"
                ],
            )
        except OTPError as error:
            return otp_error_response(
                error,
            )

        return Response(
            {
                "phone_number": (
                    result.phone_number
                ),
                "expires_in": (
                    settings
                    .OTP_CODE_TTL_SECONDS
                ),
                "resend_after": (
                    settings
                    .OTP_RESEND_COOLDOWN_SECONDS
                ),
            },
            status=status.HTTP_200_OK,
        )


class OTPVerifyAPIView(APIView):
    permission_classes = (
        AllowAny,
    )

    authentication_classes = ()

    def post(
        self,
        request: Request,
    ) -> Response:
        enforce_csrf(request)

        serializer = (
            OTPVerifySerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            user = verify_otp(
                phone_number=(
                    serializer.validated_data[
                        "phone_number"
                    ]
                ),
                code=(
                    serializer.validated_data[
                        "code"
                    ]
                ),
            )
        except OTPError as error:
            return otp_error_response(
                error,
            )

        if not user.is_active:
            return Response(
                {
                    "code": (
                        "account_disabled"
                    ),
                    "detail": (
                        "This account is "
                        "disabled."
                    ),
                },
                status=(
                    status
                    .HTTP_403_FORBIDDEN
                ),
            )

        django_login(
            request,
            user,
            backend=(
                "django.contrib.auth.backends."
                "ModelBackend"
            ),
        )

        return Response(
            {
                "authenticated": True,
                "user": (
                    CurrentUserSerializer(
                        user,
                    ).data
                ),
            },
            status=status.HTTP_200_OK,
        )


class SessionAPIView(APIView):
    permission_classes = (
        IsAuthenticated,
    )

    def get(
        self,
        request: Request,
    ) -> Response:
        return Response(
            {
                "authenticated": True,
                "user": (
                    CurrentUserSerializer(
                        request.user,
                    ).data
                ),
            },
        )


class LogoutAPIView(APIView):
    permission_classes = (
        IsAuthenticated,
    )

    def post(
        self,
        request: Request,
    ) -> Response:
        django_logout(
            request,
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )