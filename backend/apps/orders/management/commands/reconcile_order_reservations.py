from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.orders.models import Order
from apps.orders.services import (
    get_payment_reservation_duration,
)


class Command(BaseCommand):
    help = (
        "Report or backfill reservation deadlines for legacy "
        "pending-payment orders that are missing "
        "'reservation_expires_at'. Non-destructive by default: "
        "without --apply this command only reports."
    )

    def add_arguments(
        self,
        parser,
    ):
        parser.add_argument(
            "--apply",
            action="store_true",
            help=(
                "Backfill reservation_expires_at = created_at + "
                "reservation duration for the reported orders. "
                "Review the dry-run output before applying."
            ),
        )

        parser.add_argument(
            "--limit",
            type=int,
            default=500,
            help=(
                "Maximum number of orders to report or backfill "
                "in one run (default: 500)."
            ),
        )

    def handle(
        self,
        *args,
        **options,
    ):
        limit = options["limit"]

        apply_changes = options["apply"]

        duration = (
            get_payment_reservation_duration()
        )

        queryset = (
            Order.objects
            .filter(
                status=(
                    Order.Status.PENDING_PAYMENT
                ),
                reservation_expires_at__isnull=True,
            )
            .order_by("pk")
        )

        total = queryset.count()

        sample = list(
            queryset.values_list(
                "pk",
                "public_id",
                "created_at",
            )[:limit]
        )

        self.stdout.write(
            (
                f"Pending orders missing "
                f"reservation_expires_at: {total}"
            )
        )

        for pk, public_id, created_at in sample:
            deadline = created_at + duration

            self.stdout.write(
                (
                    f"  order pk={pk} "
                    f"public_id={public_id} "
                    f"created_at={created_at} "
                    f"-> backfill deadline {deadline}"
                )
            )

        if not apply_changes:
            self.stdout.write(
                self.style.WARNING(
                    (
                        "Dry run: no changes written. "
                        "Re-run with --apply to backfill "
                        "the deadlines listed above."
                    )
                )
            )
            return

        updated = 0

        for pk, _public_id, _created_at in sample:
            order = queryset.filter(
                pk=pk,
            ).first()

            if order is None:
                continue

            # Guarded, idempotent update: only rows that are
            # still missing the deadline are touched.
            updated += queryset.filter(
                pk=pk,
                reservation_expires_at__isnull=True,
            ).update(
                reservation_expires_at=(
                    order.created_at + duration
                ),
                updated_at=timezone.now(),
            )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"Backfilled reservation_expires_at "
                    f"for {updated} order(s)."
                )
            )
        )
