from rest_framework import serializers

from apps.core.geo import (
    InvalidAddress,
    validate_iran_province_city,
)
from apps.core.validators import (
    InvalidPhoneNumber,
    InvalidPostalCode,
    normalize_digits,
    normalize_iran_phone,
    normalize_iran_postal_code,
    normalize_whitespace,
)

from .models import Order, OrderItem, Shipment


ADDRESS_LINE_MAX_LENGTH = 500

CUSTOMER_NOTE_MAX_LENGTH = 1000


class CheckoutSerializer(
    serializers.Serializer,
):
    recipient_name = serializers.CharField(
        max_length=150,
    )

    phone_number = serializers.CharField(
        max_length=20,
    )

    province = serializers.CharField(
        max_length=100,
    )

    city = serializers.CharField(
        max_length=100,
    )

    postal_code = serializers.CharField(
        max_length=20,
    )

    address_line = serializers.CharField()

    building_number = serializers.CharField(
        max_length=30,
        required=False,
        allow_blank=True,
        default="",
    )

    unit_number = serializers.CharField(
        max_length=30,
        required=False,
        allow_blank=True,
        default="",
    )

    customer_note = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    def validate_recipient_name(
        self,
        value: str,
    ) -> str:
        normalized = normalize_whitespace(
            value,
        )

        if not normalized:
            raise serializers.ValidationError(
                "Recipient name is required.",
            )

        return normalized

    def validate_phone_number(
        self,
        value: str,
    ) -> str:
        """
        Authoritative Iranian mobile validation.

        Accepts Persian, Arabic and Latin digit spellings and
        stores the normalized ``+98`` form.
        """

        try:
            return normalize_iran_phone(
                value,
            )
        except InvalidPhoneNumber as exc:
            raise serializers.ValidationError(
                "Enter a valid Iranian mobile number.",
            ) from exc

    def validate_postal_code(
        self,
        value: str,
    ) -> str:
        """
        Authoritative postal-code validation: exactly ten digits,
        accepting Persian and Arabic digits and storing ASCII.
        """

        try:
            return normalize_iran_postal_code(
                value,
            )
        except InvalidPostalCode as exc:
            raise serializers.ValidationError(
                "Postal code must be exactly 10 digits.",
            ) from exc

    def validate_address_line(
        self,
        value: str,
    ) -> str:
        normalized = normalize_whitespace(
            value,
        )

        if not normalized:
            raise serializers.ValidationError(
                "Address line is required.",
            )

        if (
            len(normalized)
            > ADDRESS_LINE_MAX_LENGTH
        ):
            raise serializers.ValidationError(
                (
                    "Address line must be at most "
                    f"{ADDRESS_LINE_MAX_LENGTH} characters."
                ),
            )

        return normalized

    def _normalize_short_text(
        self,
        value: str,
    ) -> str:
        if not value:
            return ""

        return normalize_whitespace(
            normalize_digits(value),
        )

    def validate_building_number(
        self,
        value: str,
    ) -> str:
        return self._normalize_short_text(
            value,
        )

    def validate_unit_number(
        self,
        value: str,
    ) -> str:
        return self._normalize_short_text(
            value,
        )

    def validate_customer_note(
        self,
        value: str,
    ) -> str:
        normalized = normalize_whitespace(
            value,
        )

        if (
            len(normalized)
            > CUSTOMER_NOTE_MAX_LENGTH
        ):
            raise serializers.ValidationError(
                (
                    "Customer note must be at most "
                    f"{CUSTOMER_NOTE_MAX_LENGTH} characters."
                ),
            )

        return normalized

    def validate(
        self,
        attrs: dict,
    ) -> dict:
        try:
            (
                province,
                city,
            ) = validate_iran_province_city(
                attrs.get("province", ""),
                attrs.get("city", ""),
            )
        except InvalidAddress as exc:
            raise serializers.ValidationError(
                {
                    exc.field: [
                        str(exc),
                    ],
                },
            ) from exc

        attrs["province"] = province
        attrs["city"] = city

        return attrs


class OrderItemSerializer(
    serializers.ModelSerializer,
):
    line_total_rial = (
        serializers.IntegerField(
            read_only=True,
        )
    )

    class Meta:
        model = OrderItem

        fields = (
            "product_name",
            "product_slug",
            "sku",
            "material",
            "karat",
            "purity",
            "size",
            "weight_grams",
            "unit_price_rial",
            "quantity",
            "line_total_rial",
        )


class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = ("carrier", "tracking_code", "shipped_at", "delivered_at")


class OrderSerializer(
    serializers.ModelSerializer,
):
    items = OrderItemSerializer(
        many=True,
        read_only=True,
    )
    shipment = ShipmentSerializer(read_only=True)

    class Meta:
        model = Order

        fields = (
            "public_id",
            "status",
            "shipping_method",
            "shipment",
            "subtotal_rial",
            "shipping_fee_rial",
            "total_rial",
            "recipient_name",
            "phone_number",
            "province",
            "city",
            "postal_code",
            "address_line",
            "building_number",
            "unit_number",
            "customer_note",
            "items",
            "reservation_expires_at",
            "paid_at",
            "created_at",
        )