# Order Expiration Scheduler — Operations Contract

**Status: SCHEDULING IS BLOCKED (infra-dependent).** The expiry *commands*
are implemented and tested in this repository; running them *on a schedule*
requires a process supervisor (cron, systemd timer, or a task-queue beat) in
the deployment environment, which this repository does not control and does
**not** ship. Until the contract below is installed in the target
environment, `PENDING_PAYMENT` orders past their reservation deadline will
not be auto-expired and their inventory reservations will stay in place.

This document contains no references to scheduler packages or settings that
do not exist in the codebase. Everything named here is either a management
command in `backend/apps/orders/management/commands/` or infrastructure the
deployment must provide.

## Implemented management commands (in this repository)

| Command | Purpose | Status |
|---|---|---|
| `manage.py expire_pending_orders [--limit N]` | Expires due `PENDING_PAYMENT` orders and releases their inventory reservations exactly once. Default `--limit 100`. | Implemented, tested (`backend/apps/orders/tests_expire_command.py`) |
| `manage.py reconcile_order_reservations [--apply] [--limit N]` | Reports (default, non-destructive) or backfills `reservation_expires_at` for legacy pending orders that have none. Default `--limit 500`; changes require an explicit `--apply` after reviewing the dry-run. | Implemented, tested (`backend/apps/orders/tests_reconcile.py`) |

## Not implemented (must come from infrastructure)

- There is **no** scheduler package in this repository (no cron lib, no task
  queue, no beat service) and **no** scheduler settings in
  `backend/config/settings/`.
- There is **no** in-process scheduler in web workers or the test runner,
  and therefore nothing to suppress or disable: the web process never runs
  expiry by itself.
- Scheduling `expire_pending_orders` to run periodically is an environment
  concern. This is what is currently **BLOCKED**.

## Reservation deadline setting

The reservation window is configured in minutes via the standard Django
settings mechanism (`backend/apps/orders/services.py`):

- Setting name: **`ORDER_PAYMENT_RESERVATION_MINUTES`**
- Default: **15** (`DEFAULT_PAYMENT_RESERVATION_MINUTES`)
- Read through `get_payment_reservation_duration()`; invalid or non-positive
  values fall back to the default.

Orders created by `checkout_cart` carry an explicit `reservation_expires_at`.
Legacy rows with a null deadline fall back to
`created_at + ORDER_PAYMENT_RESERVATION_MINUTES` at execution time
(`get_order_reservation_deadline`), so the commands are safe to schedule
before any data reconciliation runs.

## Exact integration contract

| Item | Value |
|---|---|
| Command | `manage.py expire_pending_orders --limit=500` |
| Working directory | `backend/` |
| Interpreter | the deployment's Python with project dependencies |
| Cadence | `* * * * *` (every minute) |
| Concurrency | arbitrary/overlapping runs allowed (idempotent) |
| Failure mode | nonzero exit on unexpected errors; the job's log/alert channel is the deployment's responsibility |
| Prerequisite | `ORDER_PAYMENT_RESERVATION_MINUTES` (default 15) set as desired |

The command is **idempotent** and safe to run concurrently with live
traffic: expiry acquires the same `Order → Inventory` row-lock ordering as
checkout, fulfillment and release (`apps/orders/services.py`), each order is
expired at most once, and re-running over already-expired orders is a no-op.

### Option A — cron (to be installed in the deployment)

```cron
* * * * * cd /srv/elasi/backend && /srv/elasi/venv/bin/python manage.py expire_pending_orders --limit=500 >> /var/log/elasi/expire_orders.log 2>&1
```

### Option B — systemd timer (to be installed in the deployment)

`/etc/systemd/system/elasi-expire-orders.service`:

```ini
[Unit]
Description=Expire stale pending ELASI orders (one shot)
[Service]
Type=oneshot
WorkingDirectory=/srv/elasi/backend
ExecStart=/srv/elasi/venv/bin/python manage.py expire_pending_orders --limit=500
User=elasi
```

`/etc/systemd/system/elasi-expire-orders.timer`:

```ini
[Unit]
Description=Run ELASI order expiry every minute
[Timer]
OnCalendar=*-*-* *:*:00
AccuracySec=1s
[Install]
WantedBy=timers.target
```

```bash
systemctl enable --now elasi-expire-orders.timer
```

### Option C — the deployment's existing periodic-job runner

If the environment already runs a task scheduler, register a periodic job
whose only payload is `call_command("expire_pending_orders", limit=500)`.
Do **not** add an in-process background scheduler to the web workers:
multiple application workers would each run their own scheduler.

## Deployment checklist (unblocks the "BLOCKED" status)

1. Choose Option A, B or C in the target environment and install it.
2. Verify a run: `manage.py expire_pending_orders` exits 0 and logs no errors.
3. Wire the job's log/monitoring channel to alerts (failed runs silently
   mean reservations leak).
4. Optionally review legacy rows first with
   `manage.py reconcile_order_reservations` (dry-run) and, after explicit
   review, `--apply`.
