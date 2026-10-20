"""Install ELASI's merchant AdminSite without changing Django model registrations."""

from django.contrib.admin.apps import AdminConfig


class ElasiAdminConfig(AdminConfig):
    default_site = "apps.core.admin_site.ElasiAdminSite"
