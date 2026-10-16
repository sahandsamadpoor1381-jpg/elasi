# Order Expiration Scheduler — Operations Contract

**Status: SCHEDULING IS BLOCKED (infra-dependent).** The expiry mechanism is
implemented and tested; actually running it on a schedule requires a process
supervisor (cron/systemd/worker) in the deployment environment, which this
repository does not control. Until the contract below is installed in the
target environment, `PENDING` orders past their reservation deadline will not
be auto-expired and their inventory reservations will stay in place.

## What must run

The single expiry authority is the management command:

```bash
python manage.py expire_pending_orders [--limit N]
```

Run it from the backend directory with the production settings module and
environment. Recommended cadence: **every minute** (orders are created with a
15-minute reservation window; a 1-minute cadence bounds expiry lag to ≤ 1 min).

The command is **idempotent** and safe to run concurrently with live traffic:

- expiry acquires the same `Order → Inventory` row-lock ordering as checkout,
  fulfilment and release (`apps/orders/services.py`), so it cannot race a
  concurrent payment/fulfilment into double-releasing or leaking stock;
- each order is expired at most once (`_finalize_expiry` + `cancel_stock_reservation`
  exactly-once guards); re-running the command over already-expired orders is a no-op;
- legacy orders without `reservation_expires_at` fall back to
  `created_at + ORDER_RESERVATION_TIMEOUT_SECONDS` at execution time, so the
  command is safe to schedule before any data reconciliation; the
  non-destructive `reconcile_order_reservations` command may be reviewed and
  run separately to backfill explicit deadlines.

## Exact integration contract

| Item | Value |
|---|---|
| Command | `manage.py expire_pending_orders` |
| Working directory | `backend/` |
| Interpreter | the deployment's Python with project dependencies |
| Cadence | `* * * * *` (every minute) |
| Concurrency | arbitrary/overlapping runs allowed (idempotent) |
| Failure mode | nonzero exit on unexpected errors; cron should alert on failure |
| Prerequisite | `ORDER_RESERVATION_TIMEOUT_SECONDS` (default 900) configured |

### Option A — cron

```cron
* * * * * cd /srv/elasi/backend && /srv/elasi/venv/bin/python manage.py expire_pending_orders --limit=500 >> /var/log/elasi/expire_orders.log 2>&1
```

### Option B — systemd timer

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

### Option C — task queue (if the environment already runs one)

If the deployment has Celery/RQ/django-q, schedule a beat/cron job whose only
payload is `call_command("expire_pending_orders", limit=500)`. Do **not** add
an in-process background scheduler to the web workers: multiple gunicorn/uwsgi
workers would each run their own scheduler.

## Development note

`config/settings/base.py` contains a *dev-only* django-crontab schedule and a
`DEV_SUPPRESS_SCHEDULER` guard that disables it whenever the WSGI/ASGI entry
points import, so `runserver` autoreload or local servers never spawn an
uncontrolled scheduler. This is intentional: production expiry must come from
one of the options above, never from the web process.

## Deployment checklist (unblocks the "BLOCKED" status)

1. Choose Option A, B or C in the target environment and install it.
2. Verify a run: `manage.py expire_pending_orders` exits 0 and logs no errors.
3. Confirm the log/monitoring channel for the scheduled job is wired to alerts.
4. Keep `DEV_SUPPRESS_SCHEDULER=1` unset in production (it only affects the
   dev autoreload guard; production must use the external scheduler either way).
