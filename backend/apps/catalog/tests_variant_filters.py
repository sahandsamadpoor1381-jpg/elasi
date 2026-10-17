"""PostgreSQL regression tests for correlated multi-variant catalog filters.

Run with ``ELASI_TEST_USE_POSTGRES=1`` and the test database settings to
exercise these API cases against PostgreSQL. The same cases also run on
SQLite so the default portable suite retains coverage.
"""

from __future__ import annotations

from django.urls import reverse

from rest_framework.test import APITestCase

from apps.inventory.models import InventoryBalance

from .models import Category, Product, ProductVariant


class CatalogVariantFilterPostgreSQLTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name="QA انگشتر",
            slug="qa-rings",
        )

        cls.gold_expensive_silver_cheap = cls.make_product(
            "gold-expensive-silver-cheap",
            (
                (ProductVariant.Material.GOLD, 80_000_000, 5, 0),
                (ProductVariant.Material.SILVER, 8_000_000, 5, 0),
            ),
        )
        cls.gold_cheap_silver_expensive = cls.make_product(
            "gold-cheap-silver-expensive",
            (
                (ProductVariant.Material.GOLD, 15_000_000, 5, 0),
                (ProductVariant.Material.SILVER, 70_000_000, 5, 0),
            ),
        )
        cls.gold_sold_out_silver_available = cls.make_product(
            "gold-sold-out-silver-available",
            (
                (ProductVariant.Material.GOLD, 40_000_000, 3, 3),
                (ProductVariant.Material.SILVER, 5_000_000, 5, 0),
            ),
        )
        cls.gold_available_silver_sold_out = cls.make_product(
            "gold-available-silver-sold-out",
            (
                (ProductVariant.Material.GOLD, 25_000_000, 5, 1),
                (ProductVariant.Material.SILVER, 4_000_000, 2, 2),
            ),
        )
        cls.gold_comparator = cls.make_product(
            "gold-comparator",
            ((ProductVariant.Material.GOLD, 30_000_000, 2, 0),),
        )

    @classmethod
    def make_product(cls, slug: str, variants):
        product = Product.objects.create(
            name=slug.replace("-", " "),
            slug=slug,
            category=cls.category,
            status=Product.Status.ACTIVE,
        )

        for index, (material, price_rial, on_hand, reserved) in enumerate(
            variants,
            start=1,
        ):
            variant = ProductVariant.objects.create(
                product=product,
                sku=f"{slug.upper()}-{index}",
                material=material,
                size="17",
                price_rial=price_rial,
                is_active=True,
            )
            InventoryBalance.objects.create(
                variant=variant,
                on_hand=on_hand,
                reserved=reserved,
            )

        return product

    def listing(self, **params):
        response = self.client.get(
            reverse("catalog:product-list"),
            params,
        )
        self.assertEqual(response.status_code, 200, response.data)
        return response.json()

    def slugs(self, **params) -> list[str]:
        return [
            item["slug"]
            for item in self.listing(**params)["results"]
        ]

    def test_material_and_max_price_must_match_the_same_variant(self):
        # Gold is 80m; the product's silver option is 8m. The cheap silver
        # option must not make this product appear in a gold search capped
        # below the gold price.
        self.assertNotIn(
            self.gold_expensive_silver_cheap.slug,
            self.slugs(material="gold", max_price=20_000_000),
        )

    def test_material_and_min_price_must_match_the_same_variant(self):
        # Silver is above the minimum but the only gold option is below it.
        self.assertNotIn(
            self.gold_cheap_silver_expensive.slug,
            self.slugs(material="gold", min_price=50_000_000),
        )

    def test_material_and_availability_must_match_the_same_variant(self):
        # Gold has no available units (all three are reserved); only silver
        # is available, so this product is not an in-stock gold result.
        self.assertNotIn(
            self.gold_sold_out_silver_available.slug,
            self.slugs(material="gold", in_stock="true"),
        )

    def test_material_price_range_and_stock_require_one_matching_variant(self):
        slugs = self.slugs(
            material="gold",
            min_price=20_000_000,
            max_price=30_000_000,
            in_stock="true",
        )

        # The gold 25m option satisfies every constraint; its 4m silver
        # option is sold out and cannot supply the cheaper end of the range.
        self.assertEqual(
            set(slugs),
            {
                self.gold_available_silver_sold_out.slug,
                self.gold_comparator.slug,
            },
        )

    def test_material_filter_scopes_price_order_and_summary_but_not_variants_field(self):
        payload = self.listing(
            material="gold",
            ordering="price_asc",
        )
        by_slug = {item["slug"]: item for item in payload["results"]}
        ordered_slugs = [item["slug"] for item in payload["results"]]

        self.assertEqual(
            ordered_slugs[:3],
            [
                self.gold_cheap_silver_expensive.slug,
                self.gold_available_silver_sold_out.slug,
                self.gold_comparator.slug,
            ],
        )

        expensive = by_slug[self.gold_expensive_silver_cheap.slug]
        self.assertEqual(expensive["price_from_rial"], 80_000_000)
        self.assertEqual(expensive["price_to_rial"], 80_000_000)
        self.assertEqual(expensive["materials"], [ProductVariant.Material.GOLD])
        self.assertTrue(expensive["is_available"])
        # Backwards compatibility: the existing variants field still lists
        # all active product options, even when summary fields are filtered.
        self.assertEqual(
            {variant["material"] for variant in expensive["variants"]},
            {ProductVariant.Material.GOLD, ProductVariant.Material.SILVER},
        )

        sold_out_gold = by_slug[self.gold_sold_out_silver_available.slug]
        self.assertFalse(sold_out_gold["is_available"])
        self.assertEqual(sold_out_gold["materials"], [ProductVariant.Material.GOLD])
        self.assertEqual(sold_out_gold["price_from_rial"], 40_000_000)
