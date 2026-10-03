from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase


User = get_user_model()


class UserModelTests(TestCase):
    def test_project_uses_custom_user_model(self):
        self.assertEqual(
            User._meta.label,
            "accounts.User",
        )

    def test_user_can_be_created(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPassword123!",
            phone_number="+989123456789",
        )

        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.phone_number, "+989123456789")
        self.assertTrue(user.check_password("StrongPassword123!"))

    def test_email_must_be_unique(self):
        User.objects.create_user(
            username="firstuser",
            email="duplicate@example.com",
            password="StrongPassword123!",
        )

        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="seconduser",
                email="duplicate@example.com",
                password="StrongPassword123!",
            )

    def test_phone_number_must_be_unique_when_provided(self):
        User.objects.create_user(
            username="firstphoneuser",
            email="first@example.com",
            password="StrongPassword123!",
            phone_number="+989121111111",
        )

        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="secondphoneuser",
                email="second@example.com",
                password="StrongPassword123!",
                phone_number="+989121111111",
            )