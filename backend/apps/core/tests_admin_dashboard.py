"""Regression coverage for Admin operations visibility and permissions."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse


class MerchantAdminDashboardTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin_user = User.objects.create_superuser(
            username="merchant-admin", email="merchant@example.test", password="safe-test-secret"
        )
        self.staff_user = User.objects.create_user(
            username="restricted-staff", email="staff@example.test", password="safe-test-secret",
            is_staff=True,
        )

    def test_superuser_sees_live_empty_metrics(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "نمای کلی فروشگاه")
        self.assertContains(response, "آماده پردازش")
        self.assertContains(response, "محصولات فعال")
        self.assertContains(response, "واریانت‌های بدون موجودی آزاد")

    def test_restricted_staff_does_not_see_operations_counts(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "آماده پردازش")
        self.assertNotContains(response, "محصولات فعال")
        self.assertContains(response, "شاخص‌های عملیاتی فقط")

    def test_anonymous_access_is_redirected_to_admin_login(self):
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_order_only_staff_cannot_see_product_and_inventory_metrics(self):
        permission = Permission.objects.get(
            content_type__app_label="orders",
            codename="view_order",
        )
        self.staff_user.user_permissions.add(permission)
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "آماده پردازش")
        self.assertNotContains(response, "محصولات فعال")
        self.assertNotContains(response, "واریانت‌های بدون موجودی آزاد")
