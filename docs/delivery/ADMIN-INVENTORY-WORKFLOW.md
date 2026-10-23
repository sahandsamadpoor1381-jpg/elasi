# ELASI Admin — Catalog to Inventory Workflow (06.2)

## Merchant steps

1. Open **Catalog → Products → Add** and leave the status **Draft**.
2. Enter product data and variant SKUs and upload gallery images in the same form.
3. Save the product once. Each saved variant now shows **ثبت موجودی** (create stock), or a live **available / reserved** link.
4. Follow the link to InventoryBalance Admin. Enter the **total physical on-hand count**, **not the delta**. The existing Admin stock adjustment records a `StockMovement` ledger entry.
5. Return to the product, verify stock and imagery, and only then set the product status **Active**.

Stock availability displayed in the product listing sums `on_hand - reserved` for **active variants only**; missing balances count as zero. Stock links are navigation only: no direct balance update is introduced in Catalog Admin.

## Safety invariants

- `reserved` remains read-only and owned by order/inventory services.
- The existing transactional, row-locked `InventoryBalanceAdmin.save_model` is unchanged.
- `StockMovement` stays append-only. Balance deletion is denied, even to superusers, to protect ledger reconciliation.
- A product with no balance or with zero available stock can exist as Draft.
- This delivery does not change pricing, customer checkout, schema, or public catalog API. No migration needed.

## Validation (development test settings)

```powershell
cd D:\projects\elasi\backend
.\.venv\Scripts\python.exe manage.py test apps.catalog.tests_admin_workflow apps.inventory.tests_admin_navigation apps.inventory.tests_admin_adjustment apps.inventory.tests_admin_integration apps.catalog.tests_admin_forms --settings=config.settings.test
```

Browser acceptance: create a draft with three images, follow stock link, set on-hand 4, confirm available count and new ledger movement, then publish and verify storefront. Test permissions with a non-superuser merchant role before production release.
