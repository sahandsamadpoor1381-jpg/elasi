from rest_framework import serializers

from .models import (
    Category,
    Collection,
    Product,
    ProductImage,
    ProductVariant,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            "name",
            "slug",
        )


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = (
            "name",
            "slug",
        )


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = (
            "image",
            "alt_text",
            "sort_order",
            "is_primary",
        )


class ProductVariantSerializer(serializers.ModelSerializer):
    available = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = (
            "sku",
            "material",
            "karat",
            "purity",
            "size",
            "weight_grams",
            "price_rial",
            "compare_at_price_rial",
            "is_active",
            "available",
        )

    def get_available(self, obj: ProductVariant) -> int:
        return obj.get_available()


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    collections = CollectionSerializer(
        many=True,
        read_only=True,
    )

    images = ProductImageSerializer(
        many=True,
        read_only=True,
    )

    variants = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "name",
            "slug",
            "category",
            "collections",
            "short_description",
            "description",
            "gender",
            "allow_custom_size",
            "is_featured",
            "images",
            "variants",
        )

    def get_variants(self, obj: Product):
        if hasattr(obj, "active_variants"):
            variants = obj.active_variants
        else:
            variants = obj.variants.filter(is_active=True)
        return ProductVariantSerializer(variants, many=True).data


class ProductSummarySerializer(ProductSerializer):
    """Listing serializer: adds price range and availability aggregates.

    Every value is computed from the already-prefetched active variants,
    so a listing page stays a constant number of queries.
    """

    price_from_rial = serializers.SerializerMethodField()
    price_to_rial = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    materials = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()

    class Meta(ProductSerializer.Meta):
        fields = (
            *ProductSerializer.Meta.fields,
            "price_from_rial",
            "price_to_rial",
            "is_available",
            "materials",
            "primary_image",
        )

    def get_active_variants(self, obj: Product) -> list[ProductVariant]:
        if hasattr(obj, "active_variants"):
            return list(obj.active_variants)

        return list(
            obj.variants.filter(is_active=True).prefetch_related(
                "inventory",
            ),
        )

    def get_price_from_rial(self, obj: Product) -> int | None:
        prices = [
            variant.price_rial
            for variant in self.get_active_variants(obj)
        ]

        return min(prices) if prices else None

    def get_price_to_rial(self, obj: Product) -> int | None:
        prices = [
            variant.price_rial
            for variant in self.get_active_variants(obj)
        ]

        return max(prices) if prices else None

    def get_is_available(self, obj: Product) -> bool:
        return any(
            variant.get_available() > 0
            for variant in self.get_active_variants(obj)
        )

    def get_materials(self, obj: Product) -> list[str]:
        return sorted(
            {
                variant.material
                for variant in self.get_active_variants(obj)
            },
        )

    def get_primary_image(self, obj: Product) -> dict | None:
        images = list(obj.images.all())

        if not images:
            return None

        primary = next(
            (image for image in images if image.is_primary),
            images[0],
        )

        return ProductImageSerializer(primary).data


class CategorySummarySerializer(CategorySerializer):
    """Category with its shoppable product count."""

    product_count = serializers.IntegerField(read_only=True)

    class Meta(CategorySerializer.Meta):
        fields = (
            *CategorySerializer.Meta.fields,
            "product_count",
        )


class CollectionSummarySerializer(CollectionSerializer):
    """Collection with its shoppable product count."""

    product_count = serializers.IntegerField(read_only=True)

    class Meta(CollectionSerializer.Meta):
        fields = (
            *CollectionSerializer.Meta.fields,
            "description",
            "product_count",
        )
