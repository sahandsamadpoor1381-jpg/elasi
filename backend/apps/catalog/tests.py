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