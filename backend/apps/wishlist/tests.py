"""
Wishlist tests.

The two guarantees that matter commercially: a customer can only ever
touch their own wishlist, and adding the same product twice cannot
create duplicates. Activity states are also covered: a product that is
not shoppable cannot be added, while an already-saved product that later
becomes inactive stays visible (flagged) instead of vanishing.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.catalog.models import Category, Product, ProductVariant
from apps.inventory.models import InventoryBalance

from .models import WishlistItem

User = get_user_model()


def build_product(
    slug: str,
    *,
    status_value: str = Product.Status.ACTIVE,
    category: Category | None = None,
    price_rial: int = 100_000_000,
) -> Product:
    if category is None:
        category, _ = Category.objects.get_or_create(
            slug="wishlist-rings",
            defaults={"name": "انگشتر"},
        )

    product = Product.objects.create(
        name=f"محصول {slug}",
        slug=slug,
        category=category,
        status=status_value,
        gender=Product.Gender.UNISEX,
    )

    variant = ProductVariant.objects.create(
        product=product,
        sku=f"WISH-{slug.upper()}",
        material=ProductVariant.Material.GOLD,
        size="17",
        price_rial=price_rial,
    )

    InventoryBalance.objects.create(
        variant=variant,
        on_hand=3,
        reserved=0,
    )

    return product


class WishlistTestBase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_one = User.objects.create_user(
            username="wish-one",
            email="wish-one@example.com",
            phone_number="+989120000101",
            password="test-password",
        )
        cls.user_two = User.objects.create_user(
            username="wish-two",
            email="wish-two@example.com",
            phone_number="+989120000102",
            password="test-password",
        )
        cls.product = build_product("wish-ring")

    def list_url(self) -> str:
        return reverse("wishlist:wishlist")

    def detail_url(self, slug: str) -> str:
        return reverse(
            "wishlist:wishlist-item",
            kwargs={"product_slug": slug},
        )


class WishlistAuthenticationTests(WishlistTestBase):
    def test_anonymous_cannot_read(self):
        response = self.client.get(self.list_url())

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            response.json()["code"],
            "not_authenticated",
        )

    def test_anonymous_cannot_add(self):
        response = self.client.post(
            self.list_url(),
            {"product": "wish-ring"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(WishlistItem.objects.count(), 0)

    def test_csrf_is_enforced_for_writes(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.user_one)

        response = client.post(
            self.list_url(),
            {"product": "wish-ring"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["code"],
            "csrf_failed",
        )
        self.assertEqual(WishlistItem.objects.count(), 0)


class WishlistOwnershipTests(WishlistTestBase):
    def test_add_then_list_returns_own_item(self):
        self.client.force_login(self.user_one)

        add = self.client.post(
            self.list_url(),
            {"product": "wish-ring"},
            format="json",
        )

        self.assertEqual(add.status_code, status.HTTP_201_CREATED)

        payload = self.client.get(self.list_url()).json()

        self.assertEqual(payload["count"], 1)
        self.assertEqual(
            payload["results"][0]["product"]["slug"],
            "wish-ring",
        )

    def test_adding_twice_is_idempotent(self):
        self.client.force_login(self.user_one)

        first = self.client.post(
            self.list_url(),
            {"product": "wish-ring"},
            format="json",
        )
        second = self.client.post(
            self.list_url(),
            {"product": "wish-ring"},
            format="json",
        )

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(WishlistItem.objects.count(), 1)

    def test_wishlists_are_isolated_between_customers(self):
        WishlistItem.objects.create(
            user=self.user_two,
            product=self.product,
        )

        self.client.force_login(self.user_one)

        payload = self.client.get(self.list_url()).json()

        self.assertEqual(payload["count"], 0)

    def test_cannot_delete_another_customers_item(self):
        WishlistItem.objects.create(
            user=self.user_two,
            product=self.product,
        )

        self.client.force_login(self.user_one)

        response = self.client.delete(
            self.detail_url("wish-ring"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            WishlistItem.objects.filter(
                user=self.user_two,
            ).count(),
            1,
        )

    def test_owner_can_delete_own_item(self):
        WishlistItem.objects.create(
            user=self.user_one,
            product=self.product,
        )

        self.client.force_login(self.user_one)

        response = self.client.delete(
            self.detail_url("wish-ring"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertEqual(WishlistItem.objects.count(), 0)

    def test_delete_missing_item_returns_404(self):
        self.client.force_login(self.user_one)

        response = self.client.delete(
            self.detail_url("wish-ring"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            response.json()["code"],
            "wishlist_item_not_found",
        )


class WishlistProductStateTests(WishlistTestBase):
    def test_draft_product_cannot_be_added(self):
        build_product(
            "wish-draft",
            status_value=Product.Status.DRAFT,
        )

        self.client.force_login(self.user_one)

        response = self.client.post(
            self.list_url(),
            {"product": "wish-draft"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            response.json()["code"],
            "product_unavailable",
        )
        self.assertEqual(WishlistItem.objects.count(), 0)

    def test_product_in_inactive_category_cannot_be_added(self):
        hidden_category = Category.objects.create(
            name="دسته غیرفعال",
            slug="wishlist-hidden",
            is_active=False,
        )
        build_product(
            "wish-hidden",
            category=hidden_category,
        )

        self.client.force_login(self.user_one)

        response = self.client.post(
            self.list_url(),
            {"product": "wish-hidden"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            response.json()["code"],
            "product_unavailable",
        )

    def test_unknown_product_returns_404(self):
        self.client.force_login(self.user_one)

        response = self.client.post(
            self.list_url(),
            {"product": "does-not-exist"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            response.json()["code"],
            "product_not_found",
        )

    def test_missing_product_field_returns_400(self):
        self.client.force_login(self.user_one)

        response = self.client.post(
            self.list_url(),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            response.json()["code"],
            "product_required",
        )

    def test_saved_product_that_goes_inactive_is_flagged_not_hidden(self):
        WishlistItem.objects.create(
            user=self.user_one,
            product=self.product,
        )

        Product.objects.filter(pk=self.product.pk).update(
            status=Product.Status.ARCHIVED,
        )

        self.client.force_login(self.user_one)

        payload = self.client.get(self.list_url()).json()

        self.assertEqual(payload["count"], 1)

        item = payload["results"][0]

        self.assertFalse(item["is_purchasable"])
        self.assertEqual(item["product"]["slug"], "wish-ring")


class WishlistModelTests(TestCase):
    def test_unique_constraint_rejects_duplicate_rows(self):
        user = User.objects.create_user(
            username="wish-dup",
            email="wish-dup@example.com",
            phone_number="+989120000103",
            password="test-password",
        )
        product = build_product("wish-dup-product")

        WishlistItem.objects.create(user=user, product=product)

        from django.db import IntegrityError, transaction

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WishlistItem.objects.create(
                    user=user,
                    product=product,
                )
