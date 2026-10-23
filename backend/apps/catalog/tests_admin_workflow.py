"""Merchant workflow: product entry remains in the Django Admin."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Category, Product, ProductImage, ProductVariant


class MerchantProductEntryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_superuser(
            username="admin-product-workflow", email="admin-product@example.test",
            password="safe-test-secret",
        )
        cls.category = Category.objects.create(name="Rings", slug="workflow-rings")
        cls.product = Product.objects.create(
            name="Sample Ring", slug="admin-workflow-ring", category=cls.category,
            status=Product.Status.DRAFT,
        )
        ProductVariant.objects.create(
            product=cls.product, sku="WORKFLOW-RING", material="gold", price_rial=100000,
        )
        ProductImage.objects.create(
            product=cls.product, image="products/test/image1.jpg", is_primary=True,
        )

    def setUp(self):
        self.client.force_login(self.staff)

    def test_add_form_contains_product_variants_and_gallery(self):
        response = self.client.get(reverse("admin:catalog_product_add"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "اطلاعات محصول")
        self.assertContains(response, "گالری تصاویر")
        self.assertContains(response, "مدل‌ها، سایزها و قیمت‌ها")

    def test_list_shows_primary_image_and_status(self):
        response = self.client.get(reverse("admin:catalog_product_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "products/test/image1.jpg")
        self.assertContains(response, "Sample Ring")
