"""
Server-side checkout validation tests.

Django is the authoritative validation layer for checkout input:
these tests prove that malformed shipping data is rejected even
when a client bypasses the storefront forms.
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.cart.models import Cart, CartItem
from apps.catalog.models import (
    Category,
    Product,
    ProductVariant,
)
from apps.inventory.models import InventoryBalance


User = get_user_model()


class CheckoutValidationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="validation-user",
            email="validation@example.com",
            password="test-password",
        )

        category = Category.objects.create(
            name="Validation Rings",
            slug="validation-rings",
            sort_order=30,
        )

        product = Product.objects.create(
            name="ELASI Validation Ring",
            slug="elasi-validation-ring",
            category=category,
            status=Product.Status.ACTIVE,
        )

        cls.variant = ProductVariant.objects.create(
            product=product,
            sku="ELA-VALIDATION-G18-17",
            material=ProductVariant.Material.GOLD,
            karat=18,
            size="17",
            weight_grams="3.250",
            price_rial=250000000,
        )

        InventoryBalance.objects.create(
            variant=cls.variant,
            on_hand=5,
            reserved=0,
        )

    def valid_payload(self, **overrides):
        payload = {
            "recipient_name": "  Test   Customer  ",
            "phone_number": "09121234567",
            "province": "آذربایجان غربی",
            "city": "ارومیه",
            "postal_code": "1234567890",
            "address_line": "  Test   checkout\n address  ",
        }
        payload.update(overrides)
        return payload

    def post_checkout(self, payload):
        cart = Cart.objects.create()
        CartItem.objects.create(
            cart=cart,
            variant=self.variant,
            quantity=1,
        )

        self.client.force_authenticate(user=self.user)

        return self.client.post(
            "/api/v1/checkout/",
            payload,
            format="json",
            HTTP_X_CART_TOKEN=str(cart.token),
        )

    def test_valid_payload_creates_order(self):
        response = self.post_checkout(
            self.valid_payload(),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        payload = response.json()

        self.assertEqual(
            payload["phone_number"],
            "+989121234567",
        )

        self.assertEqual(
            payload["postal_code"],
            "1234567890",
        )

        self.assertEqual(
            payload["province"],
            "آذربایجان غربی",
        )

        self.assertEqual(
            payload["city"],
            "ارومیه",
        )

        self.assertEqual(
            payload["recipient_name"],
            "Test Customer",
        )

        self.assertEqual(
            payload["address_line"],
            "Test checkout address",
        )

    def test_persian_digits_are_normalized(self):
        response = self.post_checkout(
            self.valid_payload(
                phone_number="۰۹۱۲۱۲۳۴۵۶۷",
                postal_code="۱۲۳۴۵۶۷۸۹۰",
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        payload = response.json()

        self.assertEqual(
            payload["phone_number"],
            "+989121234567",
        )

        self.assertEqual(
            payload["postal_code"],
            "1234567890",
        )

    def test_international_phone_formats_accepted(self):
        for phone in (
            "+989121234567",
            "00989121234567",
            "989121234567",
        ):
            with self.subTest(phone=phone):
                response = self.post_checkout(
                    self.valid_payload(
                        phone_number=phone,
                    ),
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_201_CREATED,
                )

    def test_invalid_phone_rejected(self):
        for phone in (
            "12345",
            "02188776655",
            "0912123",
            "not-a-phone",
        ):
            with self.subTest(phone=phone):
                response = self.post_checkout(
                    self.valid_payload(
                        phone_number=phone,
                    ),
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )

                self.assertIn(
                    "phone_number",
                    response.json(),
                )

    def test_invalid_postal_code_rejected(self):
        for postal in (
            "123456789",
            "12345678901",
            "12345abcde",
            "",
        ):
            with self.subTest(postal=postal):
                response = self.post_checkout(
                    self.valid_payload(
                        postal_code=postal,
                    ),
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )

                self.assertIn(
                    "postal_code",
                    response.json(),
                )

    def test_unknown_province_rejected(self):
        response = self.post_checkout(
            self.valid_payload(
                province="نامعلوم",
                city="ارومیه",
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "province",
            response.json(),
        )

    def test_incompatible_province_city_rejected(self):
        response = self.post_checkout(
            self.valid_payload(
                province="تهران",
                city="ارومیه",
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "city",
            response.json(),
        )

    def test_unknown_city_rejected(self):
        response = self.post_checkout(
            self.valid_payload(
                city="شهر ناموجود",
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "city",
            response.json(),
        )

    def test_blank_required_fields_rejected(self):
        for field in (
            "recipient_name",
            "phone_number",
            "province",
            "city",
            "postal_code",
            "address_line",
        ):
            with self.subTest(field=field):
                response = self.post_checkout(
                    self.valid_payload(**{field: "   "}),
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )

    def test_whitespace_only_address_rejected(self):
        response = self.post_checkout(
            self.valid_payload(
                address_line="  \n\t  ",
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_overlong_values_rejected(self):
        cases = {
            "recipient_name": "ن" * 151,
            "address_line": "ن" * 501,
            "customer_note": "ن" * 1001,
            "building_number": "1" * 31,
            "unit_number": "1" * 31,
        }

        for field, value in cases.items():
            with self.subTest(field=field):
                response = self.post_checkout(
                    self.valid_payload(**{field: value}),
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )

    def test_building_and_unit_numbers_normalized(self):
        response = self.post_checkout(
            self.valid_payload(
                building_number=" ۱۲ ",
                unit_number="۳",
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        payload = response.json()

        self.assertEqual(
            payload["building_number"],
            "12",
        )

        self.assertEqual(
            payload["unit_number"],
            "3",
        )

    def test_customer_note_optional_and_normalized(self):
        response = self.post_checkout(
            self.valid_payload(
                customer_note="  لطفاً  با دقت  بسته‌بندی  شود.  ",
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.json()["customer_note"],
            "لطفاً با دقت بسته‌بندی شود.",
        )
