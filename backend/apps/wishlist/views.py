"""
Wishlist API.

Security model:
  * every queryset is filtered by ``request.user`` - a customer can only
    ever read or change their own wishlist, and another customer's item
    is indistinguishable from a missing one (404);
  * guests get DRF's standard 401/403 rejection with a stable
    ``not_authenticated`` code, so the storefront can offer a clear
    sign-in path instead of failing silently;
  * writes go through the session-authenticated, CSRF-enforced path like
    every other customer write in the project.

Products are exposed through the same summary serializer used by the
catalog listings, plus a per-item ``is_purchasable`` flag: a product
saved while active that later goes inactive stays visible in the
wishlist (so the customer understands why it cannot be bought) instead
of silently disappearing.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db.models import Prefetch

from apps.catalog.models import Product, ProductVariant
from apps.catalog.serializers import ProductSummarySerializer

from .models import WishlistItem


# to_attr applies to the prefetched Product, so the summary serializer
# finds product.active_variants without issuing a query per row.
WISHLIST_PRODUCT_VARIANTS = Prefetch(
    "product__variants",
    queryset=(
        ProductVariant.objects.filter(
            is_active=True,
        ).prefetch_related("inventory")
    ),
    to_attr="active_variants",
)

User = get_user_model()


class WishlistPagination(PageNumberPagination):
    page_size = 24
    page_size_query_param = "page_size"
    max_page_size = 96


class WishlistRequestError(Exception):
    """Internal signal carrying an exact client-facing error payload."""

    def __init__(
        self,
        *,
        code: str,
        detail: str,
        status_code: int,
    ) -> None:
        super().__init__(detail)

        self.code = code
        self.detail = detail
        self.status_code = status_code

    def as_response(self) -> Response:
        return Response(
            {
                "code": self.code,
                "detail": self.detail,
            },
            status=self.status_code,
        )


def is_purchasable(product: Product) -> bool:
    """Mirrors the catalog visibility rules for a single product."""

    if product.status != Product.Status.ACTIVE:
        return False

    return product.category.is_active


def serialize_item(item: WishlistItem) -> dict:
    return {
        "created_at": item.created_at,
        "is_purchasable": is_purchasable(item.product),
        "product": ProductSummarySerializer(item.product).data,
    }


def wishlist_queryset(user: User):
    return (
        WishlistItem.objects.filter(user=user)
        .select_related("product", "product__category")
        .prefetch_related(
            "product__collections",
            "product__images",
            WISHLIST_PRODUCT_VARIANTS,
        )
    )


class WishlistAPIView(APIView):
    """List the customer's wishlist, or add a product to it."""

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        queryset = wishlist_queryset(request.user)

        paginator = WishlistPagination()
        page = paginator.paginate_queryset(queryset, request)

        return paginator.get_paginated_response(
            [serialize_item(item) for item in page],
        )

    def post(self, request: Request) -> Response:
        try:
            product = self.resolve_product(request)
        except WishlistRequestError as error:
            return error.as_response()

        created = True

        try:
            with transaction.atomic():
                item, created = WishlistItem.objects.get_or_create(
                    user=request.user,
                    product=product,
                )
        except IntegrityError:
            # Concurrent double-tap: the unique constraint did its job.
            item = WishlistItem.objects.get(
                user=request.user,
                product=product,
            )
            created = False

        item = wishlist_queryset(request.user).get(pk=item.pk)

        return Response(
            serialize_item(item),
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )

    def resolve_product(self, request: Request) -> Product:
        provided = request.data.get("product") or request.data.get(
            "product_slug",
        )

        if not provided:
            raise WishlistRequestError(
                code="product_required",
                detail="product is required.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        queryset = Product.objects.select_related("category")

        if isinstance(provided, int) or (
            isinstance(provided, str) and provided.isdigit()
        ):
            product = queryset.filter(pk=int(provided)).first()
        else:
            product = queryset.filter(slug=str(provided)).first()

        if product is None:
            raise WishlistRequestError(
                code="product_not_found",
                detail="Product not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if not is_purchasable(product):
            raise WishlistRequestError(
                code="product_unavailable",
                detail="This product is not available.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return product


class WishlistItemAPIView(APIView):
    """Remove one product from the customer's own wishlist."""

    permission_classes = (IsAuthenticated,)

    def delete(
        self,
        request: Request,
        product_slug: str,
    ) -> Response:
        deleted, _ = WishlistItem.objects.filter(
            user=request.user,
            product__slug=product_slug,
        ).delete()

        if not deleted:
            # Also the response for another customer's item: ownership is
            # never disclosed.
            return Response(
                {
                    "code": "wishlist_item_not_found",
                    "detail": "This product is not in the wishlist.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
