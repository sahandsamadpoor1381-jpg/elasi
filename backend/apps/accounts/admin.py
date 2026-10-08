from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "username",
        "email",
        "phone_number",
        "is_staff",
        "is_active",
    )

    search_fields = (
        "username",
        "email",
        "phone_number",
    )

    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "ELASI",
            {
                "fields": (
                    "phone_number",
                ),
            },
        ),
    )

    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (
            "ELASI",
            {
                "fields": (
                    "email",
                    "phone_number",
                ),
            },
        ),
    )