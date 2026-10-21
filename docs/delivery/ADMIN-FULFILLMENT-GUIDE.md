# ELASI Delivery 04 — Merchant Fulfillment & Shipment Tracking

## What was added

- Single-parcel Shipment record for v1, linked 1:1 with an order.
- Atomic `dispatch_order` flow: **paid / processing → shipped**; verifies readiness, consumes reserved inventory once, creates a shipment with carrier and tracking code.
- Atomic `confirm_delivery` flow: **shipped → delivered**; never consumes inventory or changes payment.
- Merchant order change page shows shipping details and links to *Record dispatch* / *Confirm delivery*. Both transitions require POST and Django Admin change permission on the order.
- Read-only shipment records in Admin. Dispatching and delivery cannot be bypassed by ordinary direct model edits.
- Authenticated, owner-scoped API endpoints:
  - `GET /api/v1/orders/` — paginated orders of the signed-in customer.
  - `GET /api/v1/orders/<uuid>/` — one owned order; foreign order IDs return 404.
- Customer order serializer includes `shipment`: `carrier`, `tracking_code`, `shipped_at`, `delivered_at` (nullable before dispatch).

## Operational steps

1. The payment integration **must first verify** the payment server-side and transition the order to `paid` by the authorized service. Admin cannot mark an unpaid order paid.
2. In Django Admin → Orders, open a `paid` or `processing` order.
3. Use **ثبت ارسال و کد رهگیری**. Enter the actual carrier and tracking code. Confirm. The order becomes `shipped`, and the existing reserved stock is consumed **at most once**.
4. After actual delivery is confirmed, use **تأیید تحویل مرسوله**. A GET to the confirmation page makes no changes; POST performs the transition.
5. The customer can view tracking via the authenticated order detail API. Frontend account history integration is a separate acceptance task.

## Important limitations and release blockers

- This is a **single-parcel v1** model, not partial/multiple shipments.
- Tracking correction is intentionally not exposed: a duplicate dispatch with different data is rejected to avoid silently rewriting history. A dedicated audited correction process requires explicit merchant policy.
- Delivery confirmation is performed manually by authorized staff; there is no carrier webhook yet.
- The customer-facing account UI has **not** been added by this patch; API integration and browser acceptance remain open.
- This patch does **not** configure shipping fees, real payment gateways, SnappPay, TorobPay or SMS provider credentials.
- End-to-end order checkout/payment and production deployment are not established by this milestone.

## Apply and test (local)

From repository root:

```powershell
cd D:\projects\elasi

git apply --check "$env:USERPROFILE\Downloads\ELASI-delivery-04-fulfillment.patch"
git apply "$env:USERPROFILE\Downloads\ELASI-delivery-04-fulfillment.patch"
```

From `backend` with `.venv` activated:

```powershell
python manage.py makemigrations --check --dry-run --settings=config.settings.development
python manage.py check --settings=config.settings.development
python manage.py test apps.orders.tests_shipment apps.orders.tests_admin apps.orders.tests_fulfillment --settings=config.settings.test
```

Review migrations before applying to the local development database:

```powershell
python manage.py migrate --settings=config.settings.development
```

Production migrations require a backup, release authorization and rollback plan.

## Quality gates

- Confirm no migrations need generation after applying the included `0004_shipment.py` migration.
- Confirm the new fulfillment tests and previously existing order/inventory tests pass.
- Confirm staff users without order change permission cannot POST dispatch or delivery actions.
- Use a **test-only paid order** to manually verify merchant Admin dispatch and buyer order retrieval. Do not mark orders paid without verified payment in production.
- Do not report shipment workflow as browser-accepted until tested with real Django Admin in a browser.
