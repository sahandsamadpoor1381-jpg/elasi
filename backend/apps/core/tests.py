from django.urls import reverse
from rest_framework import status
from rest_framework.test import APISimpleTestCase


class HealthEndpointTests(APISimpleTestCase):
    def test_health_endpoint_returns_ok(self):
        response = self.client.get(
            reverse("core:health"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "service": "elasi-backend",
            },
        )

    def test_health_endpoint_rejects_post(self):
        response = self.client.post(
            reverse("core:health"),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )