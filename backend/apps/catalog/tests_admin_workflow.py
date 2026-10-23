"""Merchant workflow: product entry remains in the Django Admin."""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.inventory.models import InventoryBalance, StockMovement

from .admin import ProductAdmin, ProductImageInline, ProductVariantInline
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

    def test_product_form_links_to_create_stock_without_modifying_it(self):
        variant = self.product.variants.get()
        add_url = reverse("admin:inventory_inventorybalance_add")
        response = self.client.get(
            reverse("admin:catalog_product_change", args=(self.product.pk,)),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"{add_url}?variant={variant.pk}")
        self.assertContains(response, "ثبت موجودی")
        self.assertFalse(InventoryBalance.objects.filter(variant=variant).exists())
        self.assertFalse(StockMovement.objects.filter(variant=variant).exists())

    def test_product_and_variant_lists_show_available_not_reserved_stock(self):
        variant = self.product.variants.get()
        balance = InventoryBalance.objects.create(
            variant=variant, on_hand=8, reserved=3,
        )
        product_list = self.client.get(reverse("admin:catalog_product_changelist"))
        self.assertEqual(product_list.status_code, 200)
        self.assertContains(product_list, "1 مدل | 5 موجود")

        change_url = reverse(
            "admin:inventory_inventorybalance_change", args=(balance.pk,),
        )
        detail = self.client.get(
            reverse("admin:catalog_product_change", args=(self.product.pk,)),
        )
        variants = self.client.get(reverse("admin:catalog_productvariant_changelist"))
        self.assertContains(detail, change_url)
        self.assertContains(detail, "5 قابل فروش / 3 رزرو")
        self.assertContains(variants, change_url)

    def test_stock_creation_via_link_uses_admin_ledger_not_direct_model_edit(self):
        variant = self.product.variants.get()
        response = self.client.post(
            reverse("admin:inventory_inventorybalance_add"),
            {"variant": str(variant.pk), "on_hand": "4"},
        )
        self.assertEqual(response.status_code, 302)
        balance = InventoryBalance.objects.get(variant=variant)
        self.assertEqual(balance.on_hand, 4)
        movements = list(StockMovement.objects.filter(variant=variant))
        self.assertEqual(len(movements), 1)
        self.assertEqual(movements[0].reason, StockMovement.Reason.ADJUSTMENT)
        self.assertEqual(movements[0].on_hand_delta, 4)

    def test_variant_and_image_inlines_are_readable_stacked_cards(self):
        self.assertTrue(issubclass(ProductVariantInline, admin.StackedInline))
        self.assertTrue(issubclass(ProductImageInline, admin.StackedInline))
        variant_fields = ProductVariantInline.fieldsets[0][1]["fields"]
        self.assertIn(("is_active", "inventory_shortcut"), variant_fields)
        self.assertIn(("price_toman", "compare_at_price_toman"), variant_fields)
        image_fields = ProductImageInline.fieldsets[0][1]["fields"]
        self.assertIn(("image", "preview"), image_fields)

    def test_collections_use_searchable_widget_instead_of_large_dual_list(self):
        self.assertIn("collections", ProductAdmin.autocomplete_fields)
        self.assertNotIn("collections", ProductAdmin.filter_horizontal)
        response = self.client.get(
            reverse("admin:catalog_product_change", args=(self.product.pk,)),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="admin-autocomplete"')
