"""Safety regression: merchant Admin is observational for customer carts."""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.catalog.models import Category, Product, ProductVariant
from apps.orders.admin import OrderAdmin
from apps.orders.models import Order
from .admin import CartAdmin, CartItemAdmin, CartItemInline
from .models import Cart, CartItem


class MerchantCartAdminSafetyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.staff = User.objects.create_superuser(
            username="admin-cart-safety", email="admin-cart@example.test",
            password="safe-test-secret",
        )
        cls.customer = User.objects.create_user(
            username="cart-customer", email="cart-customer@example.test",
            password="safe-test-secret",
        )
        category = Category.objects.create(name="Test", slug="admin-safety")
        product = Product.objects.create(
            name="Sample", slug="admin-safety-product", category=category
        )
        variant = ProductVariant.objects.create(
            product=product, sku="ADMIN-SAFETY", material="gold", price_rial=100000,
        )
        cls.cart = Cart.objects.create(user=cls.customer)
        cls.line = CartItem.objects.create(cart=cls.cart, variant=variant, quantity=2)

    def setUp(self):
        self.client.force_login(self.staff)

    def test_cart_and_cart_items_can_be_viewed(self):
        for model, pk in [("cart", self.cart.pk), ("cartitem", self.line.pk)]:
            with self.subTest(model=model):
                url = reverse(f"admin:cart_{model}_change", args=(pk,))
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_cart_mutation_is_forbidden_and_state_is_unchanged(self):
        url = reverse("admin:cart_cart_change", args=(self.cart.pk,))
        response = self.client.post(url, {"status": Cart.Status.CONVERTED})
        self.assertEqual(response.status_code, 403)
        self.cart.refresh_from_db()
        self.assertEqual(self.cart.status, Cart.Status.ACTIVE)

    def test_cart_line_mutation_is_forbidden_and_quantity_is_unchanged(self):
        url = reverse("admin:cart_cartitem_change", args=(self.line.pk,))
        response = self.client.post(url, {"quantity": 999})
        self.assertEqual(response.status_code, 403)
        self.line.refresh_from_db()
        self.assertEqual(self.line.quantity, 2)

    def test_cart_creation_and_deletion_are_forbidden(self):
        for model, pk in [("cart", self.cart.pk), ("cartitem", self.line.pk)]:
            with self.subTest(model=model):
                self.assertEqual(
                    self.client.get(reverse(f"admin:cart_{model}_add")).status_code,
                    403,
                )
                self.assertEqual(
                    self.client.post(reverse(f"admin:cart_{model}_delete", args=(pk,))).status_code,
                    403,
                )

    def test_cart_inline_and_admin_permissions_deny_mutations(self):
        for model_admin in (
            CartAdmin(Cart, admin.site),
            CartItemAdmin(CartItem, admin.site),
            CartItemInline(Cart, admin.site),
        ):
            with self.subTest(admin=model_admin.__class__.__name__):
                request = RequestFactory().get("/admin/")
                request.user = self.staff
                self.assertFalse(model_admin.has_add_permission(request))
                self.assertFalse(model_admin.has_change_permission(request))
                self.assertFalse(model_admin.has_delete_permission(request))

    def test_orders_cannot_be_manually_created(self):
        request = RequestFactory().get("/admin/")
        request.user = self.staff
        order_admin = OrderAdmin(Order, admin.site)
        self.assertFalse(order_admin.has_add_permission(request))
        self.assertEqual(
            self.client.get(reverse("admin:orders_order_add")).status_code,
            403,
        )

    def test_financial_order_fields_are_readonly_but_shipping_details_are_editable(self):
        request = RequestFactory().get("/admin/")
        request.user = self.staff
        order_admin = OrderAdmin(Order, admin.site)
        readonly = order_admin.get_readonly_fields(request)

        # Financial snapshots, payment state, and lifecycle timestamps must
        # not be changed directly in Django Admin.
        protected_fields = (
            "public_id", "user", "status", "subtotal_rial",
            "shipping_fee_rial", "total_rial", "reservation_expires_at",
            "inventory_released_at", "inventory_consumed_at", "paid_at",
            "cancelled_at", "expired_at",
        )
        for field in protected_fields:
            with self.subTest(protected_field=field):
                self.assertIn(field, readonly)

        # Existing OrderAdmin contracts intentionally allow staff to correct
        # recipient, address and shipping details without repricing an order.
        editable_fields = (
            "shipping_method", "recipient_name", "phone_number", "province",
            "city", "postal_code", "address_line", "building_number",
            "unit_number", "customer_note",
        )
        for field in editable_fields:
            with self.subTest(editable_field=field):
                self.assertNotIn(field, readonly)
