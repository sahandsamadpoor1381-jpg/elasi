from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny

from .models import Product
from .serializers import ProductSerializer


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
            "variants__inventory",
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
            "variants__inventory",
        )
    )