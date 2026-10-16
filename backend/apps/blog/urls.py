from django.urls import path

from .views import ArticleDetailAPIView, ArticleListAPIView


app_name = "blog"


urlpatterns = [
    path(
        "articles/",
        ArticleListAPIView.as_view(),
        name="article-list",
    ),
    path(
        "articles/<slug:slug>/",
        ArticleDetailAPIView.as_view(),
        name="article-detail",
    ),
]
