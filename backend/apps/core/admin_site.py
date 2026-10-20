"""Read-only, permission-scoped merchant operations dashboard.

This is an administrative *view*, never a second source of truth for
financial or inventory data. Existing model admins and domain services
remain responsible for all mutations.
"""

from django.contrib.admin import AdminSite
from django.db.models import Count, F, Q
from django.urls import reverse


class ElasiAdminSite(AdminSite):
    site_header = "ELASI | مدیریت فروشگاه"
    site_title = "ELASI — مدیریت"
    index_title = "مرکز مدیریت فروشگاه"
    index_template = "admin/elasi_index.html"

    def index(self, request, extra_context=None):
        from apps.blog.models import Article
        from apps.catalog.models import Product
        from apps.inventory.models import InventoryBalance
        from apps.orders.models import Order

        metrics = []
        recent_orders = []

        if request.user.has_perm("orders.view_order"):
            counts = Order.objects.aggregate(
                pending=Count("pk", filter=Q(status=Order.Status.PENDING_PAYMENT)),
                to_process=Count("pk", filter=Q(status=Order.Status.PAID)),
                in_progress=Count("pk", filter=Q(status=Order.Status.PROCESSING)),
            )
            order_url = reverse("admin:orders_order_changelist")
            metrics.extend(
                [
                    {"label": "در انتظار پرداخت", "value": counts["pending"], "url": order_url},
                    {"label": "آماده پردازش", "value": counts["to_process"], "url": order_url},
                    {"label": "در حال پردازش", "value": counts["in_progress"], "url": order_url},
                ]
            )
            status_labels = {
                Order.Status.PENDING_PAYMENT: "در انتظار پرداخت",
                Order.Status.PAID: "پرداخت‌شده",
                Order.Status.PROCESSING: "در حال پردازش",
                Order.Status.SHIPPED: "ارسال‌شده",
                Order.Status.DELIVERED: "تحویل‌شده",
                Order.Status.CANCELLED: "لغوشده",
                Order.Status.EXPIRED: "منقضی‌شده",
            }
            recent_orders = [
                {
                    **order,
                    "status_label": status_labels.get(order["status"], order["status"]),
                }
                for order in Order.objects.order_by("-created_at")
                .values("pk", "public_id", "status", "created_at")[:6]
            ]

        if request.user.has_perm("catalog.view_product"):
            metrics.append(
                {
                    "label": "محصولات فعال",
                    "value": Product.objects.filter(status=Product.Status.ACTIVE).count(),
                    "url": reverse("admin:catalog_product_changelist"),
                }
            )

        if request.user.has_perm("inventory.view_inventorybalance"):
            metrics.append(
                {
                    "label": "واریانت‌های بدون موجودی آزاد",
                    "value": InventoryBalance.objects.filter(on_hand__lte=F("reserved")).count(),
                    "url": reverse("admin:inventory_inventorybalance_changelist"),
                }
            )

        if request.user.has_perm("blog.view_article"):
            metrics.append(
                {
                    "label": "مقالات پیش‌نویس",
                    "value": Article.objects.filter(status=Article.Status.DRAFT).count(),
                    "url": reverse("admin:blog_article_changelist"),
                }
            )

        context = {
            "elasi_metrics": metrics,
            "elasi_recent_orders": recent_orders,
        }
        if extra_context:
            context.update(extra_context)
        return super().index(request, extra_context=context)
