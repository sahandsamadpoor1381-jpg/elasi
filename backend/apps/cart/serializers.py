from rest_framework import serializers

from .models import Cart, CartItem


class CartItemCreateSerializer(
    serializers.Serializer,
):
    variant_sku = serializers.CharField(
        max_length=80,
    )

    quantity = serializers.IntegerField(
        min_value=1,
    )


class CartItemUpdateSerializer(
    serializers.Serializer,
):
    quantity = serializers.IntegerField(
        min_value=1,
    )


class CartItemSerializer(
    serializers.ModelSerializer,
):
    product_name = serializers.CharField(
        source="variant.product.name",
        read_only=True,
    )

    product_slug = serializers.CharField(
        source="variant.product.slug",
        read_only=True,
    )

    image = (
        serializers.SerializerMethodField()
    )

    sku = serializers.CharField(
        source="variant.sku",
        read_only=True,
    )

    material = serializers.CharField(
        source="variant.material",
        read_only=True,
    )

    karat = serializers.IntegerField(
        source="variant.karat",
        read_only=True,
        allow_null=True,
    )

    size = serializers.CharField(
        source="variant.size",
        read_only=True,
    )

    available = (
        serializers.SerializerMethodField()
    )

    unit_price_rial = (
        serializers.IntegerField(
            read_only=True,
        )
    )

    line_total_rial = (
        serializers.IntegerField(
            read_only=True,
        )
    )

    class Meta:
        model = CartItem

        fields = (
            "id",
            "product_name",
            "product_slug",
            "image",
            "sku",
            "material",
            "karat",
            "size",
            "quantity",
            "available",
            "unit_price_rial",
            "line_total_rial",
        )

    def get_available(
        self,
        obj: CartItem,
    ) -> int:
        return obj.variant.get_available()

    def get_image(
        self,
        obj: CartItem,
    ) -> str | None:
        images = list(
            obj.variant.product.images.all()
        )

        if not images:
            return None

        primary_image = next(
            (
                image
                for image in images
                if image.is_primary
            ),
            images[0],
        )

        request = self.context.get(
            "request",
        )

        image_url = (
            primary_image.image.url
        )

        if request is None:
            return image_url

        return request.build_absolute_uri(
            image_url,
        )


class CartSerializer(
    serializers.ModelSerializer,
):
    items = CartItemSerializer(
        many=True,
        read_only=True,
    )

    item_count = (
        serializers.SerializerMethodField()
    )

    total_quantity = (
        serializers.SerializerMethodField()
    )

    subtotal_rial = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = Cart

        fields = (
            "token",
            "status",
            "items",
            "item_count",
            "total_quantity",
            "subtotal_rial",
            "created_at",
            "updated_at",
        )

    def get_item_count(
        self,
        obj: Cart,
    ) -> int:
        return len(obj.items.all())

    def get_total_quantity(
        self,
        obj: Cart,
    ) -> int:
        return sum(
            item.quantity
            for item in obj.items.all()
        )

    def get_subtotal_rial(
        self,
        obj: Cart,
    ) -> int:
        return sum(
            item.line_total_rial
            for item in obj.items.all()
        )