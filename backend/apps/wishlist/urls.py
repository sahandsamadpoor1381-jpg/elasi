from django.urls import path

from .views import WishlistAPIView, WishlistItemAPIView


app_name = "wishlist"


urlpatterns = [
    path(
        "wishlist/",
        WishlistAPIView.as_view(),
        name="wishlist",
    ),
    path(
        "wishlist/items/<slug:product_slug>/",
        WishlistItemAPIView.as_view(),
        name="wishlist-item",
    ),
]
