from django.urls import path

from .views import health_check, homepage_content


app_name = "core"


urlpatterns = [
    path("health/", health_check, name="health"),
    path("homepage/", homepage_content, name="homepage"),
]
