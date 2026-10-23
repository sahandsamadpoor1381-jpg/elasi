"""Published-only homepage content and staff editing permissions."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import HomePageContent


class HomePageContentTests(TestCase):
    def test_public_endpoint_has_safe_fallback_without_published_content(self):
        response = self.client.get(reverse("core:homepage"))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")

    def test_draft_is_not_exposed_to_unauthenticated_visitors(self):
        HomePageContent.objects.create(hero_heading="PRIVATE DRAFT", is_published=False)
        response = self.client.get(reverse("core:homepage"))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")

    def test_published_content_is_returned_without_admin_fields(self):
        HomePageContent.objects.create(hero_heading="Published Hero", is_published=True)
        response = self.client.get(reverse("core:homepage"))
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["hero_heading"], "Published Hero")
        self.assertIsNone(body["hero_image"])
        self.assertNotIn("id", body)
        self.assertNotIn("is_published", body)
        self.assertNotIn("updated_at", body)

    def test_public_endpoint_is_read_only(self):
        response = self.client.post(reverse("core:homepage"), {"hero_heading": "tampered"})
        self.assertEqual(response.status_code, 405)
        self.assertFalse(HomePageContent.objects.exists())

    def test_image_requires_accessible_alt_description(self):
        record = HomePageContent(hero_image="site/home/photo.jpg", hero_image_alt="")
        with self.assertRaises(ValidationError) as error:
            record.full_clean()
        self.assertIn("hero_image_alt", error.exception.message_dict)

    def test_staff_without_change_permission_cannot_edit_homepage(self):
        user = get_user_model().objects.create_user(
            username="homepage-unprivileged", is_staff=True, password="test-password"
        )
        HomePageContent.objects.create()
        self.client.force_login(user)
        response = self.client.get(reverse("admin:core_homepagecontent_change", args=[1]))
        self.assertEqual(response.status_code, 403)

    def test_admin_allows_only_one_record(self):
        user = get_user_model().objects.create_superuser(
            username="homepage-admin", password="test-password"
        )
        self.client.force_login(user)
        add_url = reverse("admin:core_homepagecontent_add")
        self.assertEqual(self.client.get(add_url).status_code, 200)
        HomePageContent.objects.create()
        self.assertEqual(self.client.get(add_url).status_code, 403)
