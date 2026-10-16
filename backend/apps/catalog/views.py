from django.db.models import Prefetch
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny

from .models import Product, ProductVariant
from .serializers import ProductSerializer

ACTIVE_VARIANTS = Prefetch(
    "variants",
    queryset=(
        ProductVariant.objects.filter(
            is_active=True,
        ).prefetch_related("inventory")
    ),
    to_attr="active_variants",
)


class ProductListAPIView(ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = (AllowAny,)

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
        .order_by("-created_at")
    )


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
