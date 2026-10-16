"""
Listing API tests: server-side filtering, search, ordering and
pagination.

These exercise the real HTTP contract consumed by /shop, /women, /men
and /search, so a filter cannot silently work on one page and not on
another.
"""

from __future__ import annotations

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.inventory.models import InventoryBalance

from .models import (
    Category,
    Collection,
    Product,
    ProductVariant,
)


def build_variant(
    product: Product,
    sku: str,
    *,
    material: str = ProductVariant.Material.GOLD,
    price_rial: int = 100_000_000,
    on_hand: int = 5,
    reserved: int = 0,
    is_active: bool = True,
    size: str = "17",
) -> ProductVariant:
    variant = ProductVariant.objects.create(
        product=product,
        sku=sku,
        material=material,
        size=size,
        price_rial=price_rial,
        is_active=is_active,
    )

    InventoryBalance.objects.create(
        variant=variant,
        on_hand=on_hand,
        reserved=reserved,
    )

    return variant


class ListingApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.rings = Category.objects.create(
            name="انگشتر",
            slug="rings",
            sort_order=1,
        )
        cls.necklaces = Category.objects.create(
            name="گردنبند",
            slug="necklaces",
            sort_order=2,
        )
        cls.hidden_category = Category.objects.create(
            name="دسته غیرفعال",
            slug="hidden-category",
            is_active=False,
        )

        cls.classic = Collection.objects.create(
            name="کلاسیک",
            slug="classic",
            description="طرح‌های کلاسیک",
        )

        # 1) Women's gold ring, cheapest, in stock, featured.
        cls.cheap_gold_ring = Product.objects.create(
            name="انگشتر طلا ۱۸ عیار",
            slug="gold-ring-18",
            category=cls.rings,
            gender=Product.Gender.WOMEN,
            status=Product.Status.ACTIVE,
            is_featured=True,
            short_description="انگشتر ظریف طلا",
        )
        cls.cheap_gold_ring.collections.add(cls.classic)
        build_variant(
            cls.cheap_gold_ring,
            "LIST-GOLD-RING",
            price_rial=50_000_000,
            on_hand=5,
            reserved=2,
        )

        # 2) Unisex silver ring, out of stock.
        cls.silver_ring = Product.objects.create(
            name="انگشتر نقره",
            slug="silver-ring",
            category=cls.rings,
            gender=Product.Gender.UNISEX,
            status=Product.Status.ACTIVE,
        )
        build_variant(
            cls.silver_ring,
            "LIST-SILVER-RING",
            material=ProductVariant.Material.SILVER,
            price_rial=9_000_000,
            on_hand=0,
        )

        # 3) Men's gold necklace, most expensive, in stock.
        cls.gold_necklace = Product.objects.create(
            name="گردنبند طلا",
            slug="gold-necklace",
            category=cls.necklaces,
            gender=Product.Gender.MEN,
            status=Product.Status.ACTIVE,
        )
        build_variant(
            cls.gold_necklace,
            "LIST-GOLD-NECK",
            price_rial=400_000_000,
            on_hand=3,
            reserved=1,
        )

        # 4) Women's product whose only variant is inactive.
        cls.inactive_variant_product = Product.objects.create(
            name="گوشواره طلا",
            slug="inactive-variant",
            category=cls.rings,
            gender=Product.Gender.WOMEN,
            status=Product.Status.ACTIVE,
        )
        build_variant(
            cls.inactive_variant_product,
            "LIST-INACTIVE",
            is_active=False,
            price_rial=1_000_000,
        )

        # 5) Not shoppable: draft, archived, inactive category.
        cls.draft = Product.objects.create(
            name="پیش‌نویس",
            slug="draft-product",
            category=cls.rings,
            status=Product.Status.DRAFT,
        )
        cls.archived = Product.objects.create(
            name="آرشیو",
            slug="archived-product",
            category=cls.rings,
            status=Product.Status.ARCHIVED,
        )
        cls.hidden = Product.objects.create(
            name="محصول دسته غیرفعال",
            slug="inactive-category-product",
            category=cls.hidden_category,
            status=Product.Status.ACTIVE,
        )

    def listing(self, **params):
        response = self.client.get(
            reverse("catalog:product-list"),
            params,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        return response.json()

    def slugs(self, **params) -> list[str]:
        return [
            product["slug"]
            for product in self.listing(**params)["results"]
        ]


class ListingVisibilityTests(ListingApiTestCase):
    def test_only_shoppable_products_are_listed(self):
        payload = self.listing()

        slugs = {item["slug"] for item in payload["results"]}

        self.assertEqual(
            slugs,
            {
                "gold-ring-18",
                "silver-ring",
                "gold-necklace",
                "inactive-variant",
            },
        )
        self.assertNotIn("draft-product", slugs)
        self.assertNotIn("archived-product", slugs)
        self.assertNotIn("inactive-category-product", slugs)

    def test_inactive_variants_are_not_exposed(self):
        payload = self.listing()

        by_slug = {
            item["slug"]: item
            for item in payload["results"]
        }

        self.assertEqual(
            by_slug["inactive-variant"]["variants"],
            [],
        )

    def test_summary_fields_describe_price_and_availability(self):
        payload = self.listing()

        by_slug = {
            item["slug"]: item
            for item in payload["results"]
        }

        ring = by_slug["gold-ring-18"]
        self.assertEqual(ring["price_from_rial"], 50_000_000)
        self.assertEqual(ring["price_to_rial"], 50_000_000)
        self.assertTrue(ring["is_available"])
        self.assertEqual(ring["materials"], ["gold"])

        silver = by_slug["silver-ring"]
        self.assertFalse(silver["is_available"])
        self.assertEqual(silver["materials"], ["silver"])


class ListingFilterTests(ListingApiTestCase):
    def test_category_filter(self):
        self.assertEqual(
            sorted(self.slugs(category="rings")),
            sorted(
                [
                    "gold-ring-18",
                    "silver-ring",
                    "inactive-variant",
                ],
            ),
        )

    def test_collection_filter(self):
        self.assertEqual(
            self.slugs(collection="classic"),
            ["gold-ring-18"],
        )

    def test_gender_filter_includes_unisex(self):
        women = set(self.slugs(gender="women"))
        men = set(self.slugs(gender="men"))

        self.assertIn("gold-ring-18", women)
        # Unisex belongs to both listings.
        self.assertIn("silver-ring", women)
        self.assertIn("silver-ring", men)
        self.assertIn("gold-necklace", men)
        self.assertNotIn("gold-necklace", women)

    def test_gender_filter_accepts_persian_synonyms(self):
        self.assertEqual(
            set(self.slugs(gender="مردانه")),
            set(self.slugs(gender="men")),
        )

    def test_material_filter(self):
        self.assertEqual(
            self.slugs(material="silver"),
            ["silver-ring"],
        )

    def test_material_filter_accepts_persian_material_words(self):
        self.assertEqual(
            set(self.slugs(material="نقره")),
            {"silver-ring"},
        )

    def test_price_range_filter(self):
        self.assertEqual(
            self.slugs(min_price=40_000_000, max_price=100_000_000),
            ["gold-ring-18"],
        )

    def test_price_filter_accepts_persian_digits_and_separators(self):
        # "۴۰٬۰۰۰٬۰۰۰" = 40,000,000 with Persian digits and the Arabic
        # thousands separator; the silver ring (9,000,000) is below it.
        self.assertEqual(
            sorted(self.slugs(min_price="۴۰٬۰۰۰٬۰۰۰")),
            ["gold-necklace", "gold-ring-18"],
        )

    def test_invalid_price_parameter_is_ignored(self):
        self.assertEqual(
            len(self.listing(min_price="abc")["results"]),
            4,
        )

    def test_availability_filter_excludes_out_of_stock(self):
        slugs = self.slugs(in_stock="true")

        self.assertNotIn("silver-ring", slugs)
        self.assertIn("gold-ring-18", slugs)

    def test_featured_filter(self):
        self.assertEqual(
            self.slugs(is_featured="1"),
            ["gold-ring-18"],
        )

    def test_multiple_filters_combine(self):
        self.assertEqual(
            self.slugs(
                category="rings",
                gender="women",
                material="gold",
                in_stock="true",
            ),
            ["gold-ring-18"],
        )


class ListingSearchTests(ListingApiTestCase):
    def test_search_matches_product_name(self):
        self.assertIn(
            "gold-ring-18",
            self.slugs(q="انگشتر"),
        )

    def test_search_handles_arabic_yeh_and_kaf(self):
        """A shopper typing Arabic letter forms must find Persian text."""

        # "عيار": Arabic yeh (\u064a) instead of Persian yeh, matching
        # the product name "انگشتر طلا ۱۸ عیار".
        arabic_yeh_query = "\u0639\u064a\u0627\u0631"

        # "كلاسيك": Arabic kaf (\u0643) + Arabic yeh, matching the
        # collection name "کلاسیک".
        arabic_kaf_yeh_query = (
            "\u0643\u0644\u0627\u0633\u064a\u0643"
        )

        self.assertIn("\u064a", arabic_yeh_query)
        self.assertIn("\u0643", arabic_kaf_yeh_query)

        # Normalized search_text match.
        self.assertIn(
            "gold-ring-18",
            self.slugs(q=arabic_yeh_query),
        )

        # Joined collection-name match.
        self.assertIn(
            "gold-ring-18",
            self.slugs(q=arabic_kaf_yeh_query),
        )

    def test_search_handles_persian_digits(self):
        self.assertIn(
            "gold-ring-18",
            self.slugs(q="۱۸ عیار"),
        )

    def test_search_matches_material_word_in_persian(self):
        self.assertIn(
            "silver-ring",
            self.slugs(q="نقره"),
        )

    def test_search_requires_all_terms(self):
        self.assertEqual(self.slugs(q="نقره گردنبند"), [])

    def test_search_matches_category_name(self):
        self.assertIn(
            "gold-necklace",
            self.slugs(q="گردنبند"),
        )

    def test_search_matches_variant_sku(self):
        self.assertIn(
            "gold-ring-18",
            self.slugs(q="LIST-GOLD-RING"),
        )

    def test_search_excludes_non_shoppable_products(self):
        self.assertEqual(self.slugs(q="پیش‌نویس"), [])

    def test_search_without_results_is_empty(self):
        payload = self.listing(q="چیزی که وجود ندارد")

        self.assertEqual(payload["count"], 0)
        self.assertEqual(payload["results"], [])

    def test_search_endpoint_matches_listing_contract(self):
        response = self.client.get(
            reverse("catalog:product-search"),
            {"q": "طلا"},
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertEqual(
            set(payload),
            {"count", "next", "previous", "results"},
        )
        self.assertGreater(payload["count"], 0)


class ListingOrderingTests(ListingApiTestCase):
    def test_default_order_is_newest_first(self):
        slugs = self.slugs()

        self.assertEqual(
            slugs[0],
            "inactive-variant",
        )

    def test_price_ascending(self):
        slugs = self.slugs(ordering="price_asc")

        self.assertEqual(
            slugs[0],
            "silver-ring",
        )
        self.assertEqual(
            slugs[1],
            "gold-ring-18",
        )

    def test_price_descending(self):
        slugs = self.slugs(ordering="price_desc")

        self.assertEqual(
            slugs[0],
            "gold-necklace",
        )

    def test_ordering_by_name(self):
        slugs = self.slugs(ordering="name")

        self.assertEqual(len(slugs), 4)

    def test_unknown_ordering_falls_back_to_newest(self):
        self.assertEqual(
            self.slugs(ordering="whatever"),
            self.slugs(),
        )


class ListingPaginationTests(ListingApiTestCase):
    def test_page_size_is_respected(self):
        payload = self.listing(page_size=2)

        self.assertEqual(payload["count"], 4)
        self.assertEqual(len(payload["results"]), 2)
        self.assertIsNotNone(payload["next"])

    def test_second_page_returns_remaining_items(self):
        first = self.listing(page_size=3)
        second = self.listing(page_size=3, page=2)

        self.assertEqual(len(second["results"]), 1)
        self.assertIsNone(second["next"])

        self.assertTrue(
            set(
                item["slug"]
                for item in first["results"]
            ).isdisjoint(
                item["slug"]
                for item in second["results"]
            ),
        )

    def test_page_size_is_bounded(self):
        payload = self.listing(page_size=9999)

        # Page size is clamped instead of returning the whole catalog.
        self.assertLessEqual(
            len(payload["results"]),
            48,
        )

    def test_pagination_is_stable_across_filtering(self):
        payload = self.listing(
            category="rings",
            page_size=1,
        )

        self.assertEqual(payload["count"], 3)


class ListingQueryEfficiencyTests(ListingApiTestCase):
    def test_listing_query_count_is_bounded(self):
        """A listing page must not issue per-product queries (N+1).

        Six queries regardless of page size or catalog size: count,
        product page, collections, images, variants, inventory.
        """

        url = reverse("catalog:product-list")

        self.client.get(url)

        with self.assertNumQueries(6):
            self.client.get(url)

    def test_listing_query_count_does_not_grow_with_catalog(self):
        def measure() -> int:
            with CaptureQueriesContext(connection) as context:
                self.client.get(
                    reverse("catalog:product-list"),
                    {"page_size": 12},
                )

            return len(context.captured_queries)

        self.client.get(reverse("catalog:product-list"), {"page_size": 12})

        before = measure()

        for index in range(8):
            product = Product.objects.create(
                name=f"extra {index}",
                slug=f"extra-{index}",
                category=self.rings,
                status=Product.Status.ACTIVE,
            )
            build_variant(
                product,
                f"EXTRA-{index}",
                price_rial=1_000_000 * (index + 1),
            )

        self.assertEqual(measure(), before)

    def test_detail_query_count_is_bounded(self):
        url = reverse(
            "catalog:product-detail",
            kwargs={"slug": "gold-ring-18"},
        )

        self.client.get(url)

        # product + category, variants, inventory, collections, images
        with self.assertNumQueries(5):
            self.client.get(url)


class CategoryAndCollectionEndpointTests(ListingApiTestCase):
    def test_category_list_reports_product_counts(self):
        response = self.client.get(
            reverse("catalog:category-list"),
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        by_slug = {
            item["slug"]: item
            for item in payload
        }

        self.assertEqual(by_slug["rings"]["product_count"], 3)
        self.assertEqual(by_slug["necklaces"]["product_count"], 1)
        # Inactive categories are never exposed.
        self.assertNotIn("hidden-category", by_slug)

    def test_collection_list_reports_product_counts(self):
        response = self.client.get(
            reverse("catalog:collection-list"),
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["slug"], "classic")
        self.assertEqual(payload[0]["product_count"], 1)
        self.assertEqual(
            payload[0]["description"],
            "طرح‌های کلاسیک",
        )


class SearchTextMaintenanceTests(TestCase):
    def test_save_populates_normalized_search_text(self):
        category = Category.objects.create(
            name="دستبند",
            slug="bracelets",
        )

        product = Product.objects.create(
            name="دستبند نیم‌ست طلا",
            slug="bracelet-test",
            category=category,
            short_description="با یاقوت",
            status=Product.Status.ACTIVE,
        )

        product.refresh_from_db()

        self.assertIn("نیم ست", product.search_text)
        self.assertIn("یاقوت", product.search_text)

    def test_search_text_updates_on_resave(self):
        category = Category.objects.create(
            name="آویز",
            slug="pendants",
        )

        product = Product.objects.create(
            name="آویز يك",
            slug="pendant-test",
            category=category,
            status=Product.Status.ACTIVE,
        )

        product.name = "آویز دو"
        product.save()

        product.refresh_from_db()

        # Alef with madda folds to bare alef, so the stored text is the
        # same normalized form a shopper's query folds into.
        self.assertIn("اویز دو", product.search_text)
        self.assertNotIn("يك", product.search_text)
