"""Ensure inventory links cannot bypass the immutable adjustment ledger."""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.catalog.models import Category, Product, ProductVariant
from .admin import InventoryBalanceAdmin
from .models import InventoryBalance, StockMovement


class InventoryAdminNavigationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_superuser(
            username="stock-navigation-admin", email="stock-nav@example.test",
            password="safe-test-secret",
        )
        category = Category.objects.create(name="Stock navigation", slug="stock-nav")
        product = Product.objects.create(
            name="Stock example", slug="stock-example", category=category,
        )
        cls.variant = ProductVariant.objects.create(
            product=product, sku="STOCK-NAV", material="silver", price_rial=100000,
        )

    def setUp(self):
        self.client.force_login(self.staff)

    def test_balance_delete_is_denied_even_for_superuser(self):
        self.client.post(
            reverse("admin:inventory_inventorybalance_add"),
            {"variant": str(self.variant.pk), "on_hand": "5"},
        )
        balance = InventoryBalance.objects.get(variant=self.variant)
        delete_url = reverse(
            "admin:inventory_inventorybalance_delete", args=(balance.pk,),
        )
        admin_instance = InventoryBalanceAdmin(InventoryBalance, admin.site)
        request = RequestFactory().get(delete_url)
        request.user = self.staff

        self.assertFalse(admin_instance.has_delete_permission(request, balance))
        self.assertEqual(self.client.get(delete_url).status_code, 403)
        self.assertEqual(self.client.post(delete_url, {"post": "yes"}).status_code, 403)
        self.assertEqual(InventoryBalance.objects.get(pk=balance.pk).on_hand, 5)
        self.assertEqual(StockMovement.objects.filter(variant=self.variant).count(), 1)

    def test_stock_form_labels_explain_physical_count(self):
        response = self.client.get(reverse("admin:inventory_inventorybalance_add"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "موجودی فیزیکی (عدد)")
        self.assertContains(response, "تاریخچه انبار")
