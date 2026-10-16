from django.core.management.base import BaseCommand

from apps.orders.services import (
    expire_stale_pending_orders,
)


class Command(BaseCommand):
    help = (
        "Expire stale pending-payment orders "
        "and release their inventory reservations."
    )

    def add_arguments(
        self,
        parser,
    ):
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help=(
                "Maximum number of orders "
                "to expire in one run."
            ),
        )

    def handle(
        self,
        *args,
        **options,
    ):
        limit = options[
            "limit"
        ]

        expired_count = (
            expire_stale_pending_orders(
                limit=limit,
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    "Expired "
                    f"{expired_count} "
                    "pending order(s)."
                )
            )
        )