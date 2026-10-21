"""Regression tests for merchant catalogue editing (not customer price logic)."""

from django.contrib.auth import get_user_model
from django.forms.models import inlineformset_factory
from django.test import TestCase
from django.urls import reverse

from .admin_forms import (
    ProductImageAdminForm,
    ProductImageInlineFormSet,
    ProductVariantAdminForm,
)
from .models import Category, Product, ProductImage, ProductVariant


class CatalogMerchantAdminFormsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Rings Admin", slug="rings-admin")
        cls.product = Product.objects.create(
            name="Test Ring", slug="test-ring-admin", category=cls.category
        )

    def variant_data(self, **overrides):
        data = {
            "product": str(self.product.pk),
            "sku": "ELASI-ADMIN-G18",
            "material": ProductVariant.Material.GOLD,
            "karat": "18",
            "size": "17",
            "price_toman": "25000000",
            "compare_at_price_toman": "30000000",
            "is_active": "on",
        }
        data.update(overrides)
        return data

    def test_new_variant_converts_toman_to_rial_exactly_once(self):
        form = ProductVariantAdminForm(data=self.variant_data())
        self.assertTrue(form.is_valid(), form.errors)
        variant = form.save()
        self.assertEqual(variant.price_rial, 250000000)
        self.assertEqual(variant.compare_at_price_rial, 300000000)
        self.assertEqual(ProductVariant.objects.get(pk=variant.pk).price_rial, 250000000)

    def test_existing_variant_price_prefills_in_toman_and_updates(self):
        variant = ProductVariant.objects.create(
            product=self.product, sku="TEST-OLD", material=ProductVariant.Material.SILVER,
            price_rial=12341,
        )
        initial_form = ProductVariantAdminForm(instance=variant)
        self.assertEqual(str(initial_form.initial["price_toman"]), "1234.1")
        form = ProductVariantAdminForm(
            instance=variant,
            data=self.variant_data(sku="TEST-OLD", price_toman="2000.5", compare_at_price_toman=""),
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        variant.refresh_from_db()
        self.assertEqual(variant.price_rial, 20005)
        self.assertIsNone(variant.compare_at_price_rial)

    def test_invalid_money_is_not_silently_rounded(self):
        for bad_price in ("1.23", "0", "-1", "abc", "999999999999999999"):
            with self.subTest(bad_price=bad_price):
                form = ProductVariantAdminForm(data=self.variant_data(price_toman=bad_price))
                self.assertFalse(form.is_valid())
                self.assertIn("price_toman", form.errors)

    def test_compare_at_price_must_be_above_sale_price(self):
        form = ProductVariantAdminForm(
            data=self.variant_data(compare_at_price_toman="25000000")
        )
        self.assertFalse(form.is_valid())
        self.assertIn("compare_at_price_toman", form.errors)

    def test_standalone_image_change_rejects_second_primary(self):
        ProductImage.objects.create(
            product=self.product, image="products/test/primary.jpg", is_primary=True
        )
        secondary = ProductImage.objects.create(
            product=self.product, image="products/test/secondary.jpg", is_primary=False
        )
        form = ProductImageAdminForm(
            instance=secondary,
            data={
                "product": str(self.product.pk),
                "alt_text": "Other angle",
                "sort_order": "1",
                "is_primary": "on",
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn("is_primary", form.errors)

    def test_inline_rejects_two_primary_images(self):
        a = ProductImage.objects.create(product=self.product, image="products/test/a.jpg")
        b = ProductImage.objects.create(product=self.product, image="products/test/b.jpg")
        formset_class = inlineformset_factory(
            Product, ProductImage,
            formset=ProductImageInlineFormSet,
            fields=("image", "alt_text", "sort_order", "is_primary"),
            extra=0,
        )
        data = {
            "images-TOTAL_FORMS": "2",
            "images-INITIAL_FORMS": "2",
            "images-MIN_NUM_FORMS": "0",
            "images-MAX_NUM_FORMS": "1000",
            "images-0-id": str(a.pk),
            "images-0-product": str(self.product.pk),
            "images-0-sort_order": "0",
            "images-0-is_primary": "on",
            "images-1-id": str(b.pk),
            "images-1-product": str(self.product.pk),
            "images-1-sort_order": "1",
            "images-1-is_primary": "on",
        }
        formset = formset_class(data=data, instance=self.product, prefix="images")
        self.assertFalse(formset.is_valid())
        # No unrelated field errors: the rejection must come from the
        # duplicate-primary formset rule, not missing required fields.
        self.assertFalse(any(formset.errors), formset.errors)
        self.assertIn("فقط یک تصویر اصلی", str(formset.non_form_errors()))

    def test_inline_primary_replacement_uses_safe_two_step_flow(self):
        old = ProductImage.objects.create(
            product=self.product, image="products/test/primary-old.jpg", is_primary=True
        )
        new = ProductImage.objects.create(
            product=self.product, image="products/test/primary-new.jpg", is_primary=False
        )
        formset_class = inlineformset_factory(
            Product, ProductImage,
            formset=ProductImageInlineFormSet,
            fields=("image", "alt_text", "sort_order", "is_primary"), extra=0,
        )
        data = {
            "images-TOTAL_FORMS": "2", "images-INITIAL_FORMS": "2",
            "images-MIN_NUM_FORMS": "0", "images-MAX_NUM_FORMS": "1000",
            "images-0-id": str(old.pk), "images-0-product": str(self.product.pk),
            "images-0-sort_order": "0",
            "images-1-id": str(new.pk), "images-1-product": str(self.product.pk),
            "images-1-sort_order": "1",
            "images-1-is_primary": "on",
        }
        formset = formset_class(data=data, instance=self.product, prefix="images")
        self.assertFalse(formset.is_valid())
        # Either the model's conditional uniqueness validation or the
        # inline formset must reject the unsafe one-step replacement.
        self.assertTrue(formset.non_form_errors() or any(formset.errors))

    def test_admin_forms_expose_toman_not_rial(self):
        user_model = get_user_model()
        superuser = user_model.objects.create_superuser(
            username="catalog-manager", email="catalog@example.test", password="test-password"
        )
        self.client.force_login(superuser)
        response = self.client.get(reverse("admin:catalog_productvariant_add"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="price_toman"')
        self.assertNotContains(response, 'name="price_rial"')
        response = self.client.get(reverse("admin:catalog_product_change", args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "price_toman")
