from django.urls import path

from .views import (
    CategoryListAPIView,
    CollectionListAPIView,
    ProductDetailAPIView,
    ProductListAPIView,
    ProductSearchAPIView,
)


app_name = "catalog"


urlpatterns = [
    path(
        "products/",
        ProductListAPIView.as_view(),
        name="product-list",
    ),
    # Declared before the slug route so "search" is never treated as a
    # product slug.
    path(
        "products/search/",
        ProductSearchAPIView.as_view(),
        name="product-search",
    ),
    path(
        "products/<slug:slug>/",
        ProductDetailAPIView.as_view(),
        name="product-detail",
    ),
    path(
        "categories/",
        CategoryListAPIView.as_view(),
        name="category-list",
    ),
    path(
        "collections/",
        CollectionListAPIView.as_view(),
        name="collection-list",
    ),
]
