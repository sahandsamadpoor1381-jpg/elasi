from rest_framework import serializers

from .models import User


class OTPRequestSerializer(
    serializers.Serializer,
):
    phone_number = serializers.CharField(
        max_length=30,
        trim_whitespace=True,
    )


class OTPVerifySerializer(
    serializers.Serializer,
):
    phone_number = serializers.CharField(
        max_length=30,
        trim_whitespace=True,
    )

    code = serializers.RegexField(
        regex=r"^\d{6}$",
        max_length=6,
        min_length=6,
    )


class CurrentUserSerializer(
    serializers.ModelSerializer,
):
    class Meta:
        model = User

        fields = (
            "id",
            "phone_number",
            "email",
            "first_name",
            "last_name",
        )

        read_only_fields = fields