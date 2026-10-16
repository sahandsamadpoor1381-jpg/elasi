from __future__ import annotations

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from apps.catalog.models import Category, Product, ProductVariant
from apps.catalog.serializers import ProductSerializer
from apps.catalog.views import ProductDetailAPIView, ProductListAPIView
from apps.inventory.models import InventoryBalance


class VariantVisibilityContractTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category, _ = Category.objects.get_or_create(
            name="Visibility Rings",
            defaults={"slug": "visibility-rings", "sort_order": 60},
        )
        cls.product = Product.objects.create(
            name="VisP",
            slug="vis-p",
            category=cls.category,
            status=Product.Status.ACTIVE,
        )
        cls.active_variant = ProductVariant.objects.create(
            product=cls.product,
            sku="VIS-ACTIVE",
            material=ProductVariant.Material.GOLD,
            size="16",
            price_rial=100,
            is_active=True,
        )
        cls.inactive_variant = ProductVariant.objects.create(
            product=cls.product,
            sku="VIS-INACTIVE",
            material=ProductVariant.Material.GOLD,
            size="17",
            price_rial=100,
            is_active=False,
        )
        InventoryBalance.objects.create(variant=cls.active_variant, on_hand=4, reserved=1)
        InventoryBalance.objects.create(variant=cls.inactive_variant, on_hand=9, reserved=0)

    def test_get_available_is_zero_for_inactive_variant(self):
        self.inactive_variant.refresh_from_db()
        self.assertEqual(self.inactive_variant.get_available(), 0)
        self.assertEqual(self.active_variant.get_available(), 3)

    def test_serializer_exposes_is_active_and_honest_availability(self):
        data = ProductSerializer(self.product).data
        by_sku = {v["sku"]: v for v in data["variants"]}
        self.assertNotIn("VIS-INACTIVE", by_sku)
        self.assertTrue(by_sku["VIS-ACTIVE"]["is_active"])
        self.assertEqual(by_sku["VIS-ACTIVE"]["available"], 3)

    def test_catalog_endpoints_hide_inactive_variants(self):
        factory = APIRequestFactory()
        request = factory.get("/api/v1/products/")

        list_view = ProductListAPIView()
        list_view.kwargs = {}
        list_view.request = request
        list_view.format_kwarg = None
        queryset = list_view.get_queryset()
        products = list(queryset)
        serializer = ProductSerializer(products, many=True)
        skus = [v["sku"] for p in serializer.data for v in p["variants"]]
        self.assertIn("VIS-ACTIVE", skus)
        self.assertNotIn("VIS-INACTIVE", skus)

        detail_view = ProductDetailAPIView()
        detail_view.kwargs = {"slug": "vis-p"}
        detail_view.request = request
        detail_view.format_kwarg = None
        obj = detail_view.get_object()
        detail_data = ProductSerializer(obj).data
        detail_skus = [v["sku"] for v in detail_data["variants"]]
        self.assertIn("VIS-ACTIVE", detail_skus)
        self.assertNotIn("VIS-INACTIVE", detail_skus)
