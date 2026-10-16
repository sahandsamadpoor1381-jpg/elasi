from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny

from .models import Article
from .serializers import (
    ArticleDetailSerializer,
    ArticleListSerializer,
)


class ArticlePagination(PageNumberPagination):
    page_size = 9
    page_size_query_param = "page_size"
    max_page_size = 36


class ArticleListAPIView(ListAPIView):
    """Published articles only, newest first."""

    serializer_class = ArticleListSerializer
    permission_classes = (AllowAny,)
    pagination_class = ArticlePagination

    def get_queryset(self):
        # Built per request: the "published by now" boundary must be
        # evaluated when the request is served. A class-level queryset
        # would freeze timezone.now() at import, so an article published
        # after the process started would stay invisible until restart.
        return Article.objects.published().only(
            "title",
            "slug",
            "excerpt",
            "cover_image",
            "published_at",
        )


class ArticleDetailAPIView(RetrieveAPIView):
    serializer_class = ArticleDetailSerializer
    permission_classes = (AllowAny,)
    lookup_field = "slug"

    def get_queryset(self):
        return Article.objects.published()
