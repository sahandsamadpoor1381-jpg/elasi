"""
Public catalog API.

Every listing query is server-side and shared by all storefront entry
points (/shop, /women, /men, /search and the homepage), so filters,
sorting, availability and pagination cannot drift between pages:

  * only ACTIVE products in ACTIVE categories are ever exposed;
  * only ACTIVE variants are exposed, and an inactive variant reports
    zero availability;
  * filters: category, collection, gender, material, price range,
    availability, featured;
  * ordering: newest (default), price ascending/descending, name;
  * search: Persian/Arabic-normalized, term-wise (AND) matching across
    the product text plus its category, collections and variant
    attributes;
  * pagination: page / page_size with a bounded page size.

Efficiency: one query for the page plus prefetch/select_related for
category, collections, images and active variants - no N+1. Price and
availability ordering use annotations rather than per-row Python.
"""

from __future__ import annotations

from django.db.models import (
    Count,
    F,
    IntegerField,
    OuterRef,
    Prefetch,
    Q,
    QuerySet,
    Subquery,
)

from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny

from apps.core.text import normalize_fa, search_terms

from .models import Category, Collection, Product, ProductVariant
from .serializers import (
    CategorySummarySerializer,
    CollectionSummarySerializer,
    ProductSerializer,
    ProductSummarySerializer,
)

ACTIVE_VARIANTS = Prefetch(
    "variants",
    queryset=(
        ProductVariant.objects.filter(
            is_active=True,
        ).prefetch_related("inventory")
    ),
    to_attr="active_variants",
)

# Material words shoppers actually type, mapped to stored enum values.
MATERIAL_SYNONYMS = {
    "طلا": "gold",
    "طلایی": "gold",
    "gold": "gold",
    "نقره": "silver",
    "نقره‌ای": "silver",
    "نقرهای": "silver",
    "silver": "silver",
}

GENDER_SYNONYMS = {
    "زنانه": "women",
    "زنان": "women",
    "women": "women",
    "مردانه": "men",
    "مردان": "men",
    "men": "men",
    "یونیسکس": "unisex",
    "unisex": "unisex",
}

# Ordinal letter variants a shopper may type; both forms are searched so
# stored text written with one form still matches a query using the other.
LETTER_VARIANTS = (
    ("ی", "ي"),
    ("ک", "ك"),
)


class ProductPagination(PageNumberPagination):
    """Bounded page-number pagination for product listings."""

    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 48


def _query_variants(term: str) -> list[str]:
    """Return the term plus its Arabic-form spellings (deduplicated)."""

    variants = {term}

    for persian, arabic in LETTER_VARIANTS:
        if persian in term:
            variants.add(term.replace(persian, arabic))

        if arabic in term:
            variants.add(term.replace(arabic, persian))

    return sorted(variants)


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None

    digits = normalize_fa(value)

    for separator in (",", "\u066c", "\u060c", " "):
        digits = digits.replace(separator, "")

    digits = digits.strip()

    if not digits:
        return None

    try:
        return int(digits)
    except ValueError:
        return None


def _parse_bool(value: str | None) -> bool:
    if value is None:
        return False

    return normalize_fa(value) in {"1", "true", "yes", "on"}


def _filter_gender(queryset: QuerySet, gender: str) -> QuerySet:
    """Apply storefront gender semantics.

    A women's listing means "jewelry for women", which legitimately
    includes unisex pieces (and the same for men). This keeps unisex
    products discoverable from both listings instead of vanishing from
    each of them.
    """

    if gender == Product.Gender.WOMEN:
        return queryset.filter(
            gender__in=[
                Product.Gender.WOMEN,
                Product.Gender.UNISEX,
            ],
        )

    if gender == Product.Gender.MEN:
        return queryset.filter(
            gender__in=[
                Product.Gender.MEN,
                Product.Gender.UNISEX,
            ],
        )

    return queryset.filter(gender=gender)


class ProductQuerysetMixin:
    """Builds the filtered, ordered product queryset from query params."""

    def get_queryset(self) -> QuerySet:
        queryset = (
            Product.objects.filter(
                status=Product.Status.ACTIVE,
                category__is_active=True,
            )
            .select_related("category")
            .prefetch_related(
                "collections",
                "images",
                ACTIVE_VARIANTS,
            )
        )

        params = getattr(
            self.request,
            "query_params",
            None,
        )

        if params is None:
            # Plain WSGIRequest (e.g. a view instantiated directly).
            params = self.request.GET

        return self.apply_filters(queryset, params)

    def apply_filters(
        self,
        queryset: QuerySet,
        params,
    ) -> QuerySet:
        queryset = self.apply_catalog_filters(queryset, params)
        queryset = self.apply_search(queryset, params)

        return self.apply_ordering(queryset, params)

    def apply_catalog_filters(
        self,
        queryset: QuerySet,
        params,
    ) -> QuerySet:
        category = params.get("category")

        if category:
            slugs = [
                slug.strip()
                for slug in category.split(",")
                if slug.strip()
            ]

            if slugs:
                queryset = queryset.filter(
                    category__slug__in=slugs,
                )

        collection = params.get("collection")

        if collection:
            slugs = [
                slug.strip()
                for slug in collection.split(",")
                if slug.strip()
            ]

            if slugs:
                queryset = queryset.filter(
                    collections__slug__in=slugs,
                )

        gender = params.get("gender")

        if gender:
            normalized_gender = normalize_fa(gender)

            normalized_gender = GENDER_SYNONYMS.get(
                normalized_gender,
                normalized_gender,
            )

            if normalized_gender in dict(
                Product.Gender.choices,
            ):
                queryset = _filter_gender(
                    queryset,
                    normalized_gender,
                )

        material = params.get("material")

        if material:
            materials = {
                MATERIAL_SYNONYMS.get(
                    normalize_fa(item),
                    normalize_fa(item),
                )
                for item in material.split(",")
                if item.strip()
            }

            if materials:
                queryset = queryset.filter(
                    variants__is_active=True,
                    variants__material__in=materials,
                )

        min_price = _parse_int(params.get("min_price"))

        if min_price is not None:
            queryset = queryset.filter(
                variants__is_active=True,
                variants__price_rial__gte=min_price,
            )

        max_price = _parse_int(params.get("max_price"))

        if max_price is not None:
            queryset = queryset.filter(
                variants__is_active=True,
                variants__price_rial__lte=max_price,
            )

        if _parse_bool(params.get("in_stock")):
            queryset = queryset.filter(
                variants__is_active=True,
                variants__inventory__on_hand__gt=F(
                    "variants__inventory__reserved",
                ),
            )

        if _parse_bool(params.get("is_featured")):
            queryset = queryset.filter(is_featured=True)

        # Filters that traverse variants/collections can duplicate rows.
        if any(
            params.get(key)
            for key in (
                "collection",
                "material",
                "min_price",
                "max_price",
            )
        ) or _parse_bool(params.get("in_stock")):
            queryset = queryset.distinct()

        return queryset

    def apply_search(
        self,
        queryset: QuerySet,
        params,
    ) -> QuerySet:
        raw_query = (
            params.get("q")
            or params.get("search")
            or ""
        )

        terms = search_terms(raw_query)

        if not terms:
            return queryset

        combined = Q()

        for term in terms:
            term_matches = Q()

            for variant in _query_variants(term):
                term_matches |= Q(
                    search_text__icontains=variant,
                )
                term_matches |= Q(
                    category__name__icontains=variant,
                )
                term_matches |= Q(
                    collections__name__icontains=variant,
                )
                term_matches |= Q(
                    variants__sku__icontains=variant,
                )
                term_matches |= Q(
                    variants__size__icontains=variant,
                )

            material = MATERIAL_SYNONYMS.get(term)

            if material:
                term_matches |= Q(
                    variants__material=material,
                )

            combined &= term_matches

        return queryset.filter(combined).distinct()

    def apply_ordering(
        self,
        queryset: QuerySet,
        params,
    ) -> QuerySet:
        ordering = normalize_fa(
            params.get("ordering") or "",
        )

        # OuterRef correlates the subquery with the product row being
        # ordered; a plain F() here would resolve inside the subquery and
        # return the same (globally cheapest) price for every product.
        price_subquery = (
            ProductVariant.objects.filter(
                product_id=OuterRef("pk"),
                is_active=True,
            )
            .order_by("price_rial")
            .values("price_rial")[:1]
        )

        if ordering in {
            "price_asc",
            "price_desc",
            "price",
        }:
            # NULL means "no active variant has a price" (nothing is
            # purchasable); those products sort last instead of being
            # presented as the cheapest ones.
            queryset = queryset.annotate(
                ordering_price=Subquery(
                    price_subquery,
                    output_field=IntegerField(),
                ),
            )

            if ordering == "price_desc":
                return queryset.order_by(
                    F("ordering_price").desc(
                        nulls_last=True,
                    ),
                    "-created_at",
                )

            return queryset.order_by(
                F("ordering_price").asc(
                    nulls_last=True,
                ),
                "-created_at",
            )

        if ordering in {"name", "name_asc"}:
            return queryset.order_by("name")

        if ordering in {"oldest", "oldest_first"}:
            return queryset.order_by("created_at")

        if ordering in {"featured", "featured_first"}:
            return queryset.order_by(
                "-is_featured",
                "-created_at",
            )

        return queryset.order_by("-created_at")


class ProductListAPIView(
    ProductQuerysetMixin,
    ListAPIView,
):
    """Filtered, searchable, paginated product listing."""

    serializer_class = ProductSummarySerializer
    permission_classes = (AllowAny,)
    pagination_class = ProductPagination


class ProductDetailAPIView(RetrieveAPIView):
    serializer_class = ProductSerializer
    permission_classes = (AllowAny,)
    lookup_field = "slug"

    queryset = (
        Product.objects.filter(
            status=Product.Status.ACTIVE,
            category__is_active=True,
        )
        .select_related("category")
        .prefetch_related(
            "collections",
            "images",
            ACTIVE_VARIANTS,
        )
    )


class CategoryListAPIView(ListAPIView):
    """Active categories, each with its number of shoppable products."""

    serializer_class = CategorySummarySerializer
    permission_classes = (AllowAny,)
    pagination_class = None

    queryset = (
        Category.objects.filter(is_active=True)
        .annotate(
            product_count=Count(
                "products",
                filter=Q(
                    products__status=Product.Status.ACTIVE,
                ),
                distinct=True,
            ),
        )
        .order_by("sort_order", "name")
    )


class CollectionListAPIView(ListAPIView):
    """Active collections, each with its number of shoppable products."""

    serializer_class = CollectionSummarySerializer
    permission_classes = (AllowAny,)
    pagination_class = None

    queryset = (
        Collection.objects.filter(is_active=True)
        .annotate(
            product_count=Count(
                "products",
                filter=Q(
                    products__status=Product.Status.ACTIVE,
                ),
                distinct=True,
            ),
        )
        .order_by("name")
    )


class ProductSearchAPIView(ProductQuerysetMixin, ListAPIView):
    """Dedicated search endpoint (same contract as the listing)."""

    serializer_class = ProductSummarySerializer
    permission_classes = (AllowAny,)
    pagination_class = ProductPagination
