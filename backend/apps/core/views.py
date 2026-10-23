from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(_request: Request) -> Response:
    return Response(
        {
            "status": "ok",
            "service": "elasi-backend",
        }
    )

@api_view(["GET"])
@permission_classes([AllowAny])
def homepage_content(_request: Request) -> Response:
    """Only published content is public; absence keeps the current static storefront."""
    from .models import HomePageContent
    from .serializers import HomePageContentSerializer

    content = HomePageContent.objects.filter(is_published=True).first()
    if content is None:
        # An unpublished page must not leak drafts or pretend to serve JSON.
        # The storefront deliberately falls back to its existing content.
        return Response(status=status.HTTP_204_NO_CONTENT)

    return Response(HomePageContentSerializer(content).data)
