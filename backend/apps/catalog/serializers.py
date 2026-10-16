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