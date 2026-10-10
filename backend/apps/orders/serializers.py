from rest_framework import serializers

from .models import Order, OrderItem


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


class OrderSerializer(
    serializers.ModelSerializer,
):
    items = OrderItemSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Order

        fields = (
            "public_id",
            "status",
            "shipping_method",
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
            "created_at",
        )