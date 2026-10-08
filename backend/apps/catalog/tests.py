from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from .models import (
    Category,
    Collection,
    Product,
    ProductImage,
    ProductVariant,
)


class CatalogModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name="Rings",
            slug="rings",
            sort_order=10,
        )

        cls.collection = Collection.objects.create(
            name="Signature",
            slug="signature",
        )

        cls.product = Product.objects.create(
            name="ELASI Luna Ring",
            slug="elasi-luna-ring",
            category=cls.category,
            gender=Product.Gender.WOMEN,
            status=Product.Status.ACTIVE,
            allow_custom_size=True,
            is_featured=True,
        )

        cls.product.collections.add(cls.collection)

        cls.variant = ProductVariant.objects.create(
            product=cls.product,
            sku="ELA-RNG-LUNA-G18-17",
            material=ProductVariant.Material.GOLD,
            karat=18,
            size="17",
            weight_grams="3.250",
            price_rial=250000000,
        )

    def test_product_relationships(self):
        self.assertEqual(
            self.product.category,
            self.category,
        )

        self.assertIn(
            self.collection,
            self.product.collections.all(),
        )

        self.assertIn(
            self.variant,
            self.product.variants.all(),
        )

    def test_variant_belongs_to_product(self):
        self.assertEqual(
            self.variant.product,
            self.product,
        )

        self.assertEqual(
            self.variant.sku,
            "ELA-RNG-LUNA-G18-17",
        )

    def test_category_with_products_cannot_be_deleted(self):
        with self.assertRaises(ProtectedError):
            self.category.delete()

    def test_product_can_have_images(self):
        image = ProductImage.objects.create(
            product=self.product,
            image="products/test/luna-front.jpg",
            alt_text="ELASI Luna Ring front view",
            sort_order=10,
            is_primary=True,
        )

        self.assertIn(
            image,
            self.product.images.all(),
        )

        self.assertEqual(
            image.alt_text,
            "ELASI Luna Ring front view",
        )

    def test_product_cannot_have_multiple_primary_images(self):
        ProductImage.objects.create(
            product=self.product,
            image="products/test/luna-front.jpg",
            is_primary=True,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProductImage.objects.create(
                    product=self.product,
                    image="products/test/luna-side.jpg",
                    is_primary=True,
                )

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class CatalogAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name="API Rings",
            slug="api-rings",
            sort_order=10,
        )

        cls.active_product = Product.objects.create(
            name="Public Ring",
            slug="public-ring",
            category=cls.category,
            status=Product.Status.ACTIVE,
        )

        cls.variant = ProductVariant.objects.create(
            product=cls.active_product,
            sku="API-RING-G18-17",
            material=ProductVariant.Material.GOLD,
            karat=18,
            size="17",
            price_rial=250000000,
        )

        from apps.inventory.models import InventoryBalance

        InventoryBalance.objects.create(
            variant=cls.variant,
            on_hand=5,
            reserved=2,
        )

        cls.draft_product = Product.objects.create(
            name="Draft Ring",
            slug="draft-ring",
            category=cls.category,
            status=Product.Status.DRAFT,
        )

    def test_product_list_is_public(self):
        response = self.client.get(
            reverse("catalog:product-list"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_product_list_contains_active_product(self):
        response = self.client.get(
            reverse("catalog:product-list"),
        )

        slugs = [
            product["slug"]
            for product in response.json()
        ]

        self.assertIn(
            "public-ring",
            slugs,
        )

    def test_product_list_excludes_draft_product(self):
        response = self.client.get(
            reverse("catalog:product-list"),
        )

        slugs = [
            product["slug"]
            for product in response.json()
        ]

        self.assertNotIn(
            "draft-ring",
            slugs,
        )

    def test_product_detail_returns_inventory_availability(self):
        response = self.client.get(
            reverse(
                "catalog:product-detail",
                kwargs={"slug": "public-ring"},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.json()["variants"][0]["available"],
            3,
        )

    def test_draft_product_detail_returns_not_found(self):
        response = self.client.get(
            reverse(
                "catalog:product-detail",
                kwargs={"slug": "draft-ring"},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )