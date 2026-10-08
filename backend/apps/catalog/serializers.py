from django.core.exceptions import ObjectDoesNotExist
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
            "available",
        )

    def get_available(self, obj: ProductVariant) -> int:
        try:
            return obj.inventory.available
        except ObjectDoesNotExist:
            return 0


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

    variants = ProductVariantSerializer(
        many=True,
        read_only=True,
    )

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