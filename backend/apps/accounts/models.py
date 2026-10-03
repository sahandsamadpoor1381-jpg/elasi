from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        unique=True,
    )

    phone_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return self.email or self.username