from django.urls import path

from .views import ProductDetailAPIView, ProductListAPIView


app_name = "catalog"


urlpatterns = [
    path(
        "products/",
        ProductListAPIView.as_view(),
        name="product-list",
    ),
    path(
        "products/<slug:slug>/",
        ProductDetailAPIView.as_view(),
        name="product-detail",
    ),
]