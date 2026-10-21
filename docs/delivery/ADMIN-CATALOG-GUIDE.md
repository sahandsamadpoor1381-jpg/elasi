# ELASI — Catalog administration (Delivery 02)

Status: implementation prepared; Django database tests and merchant browser acceptance pending.

- At `/admin/catalog/product/`, create a product, assign a category, and edit its variants and images together.
- Variant forms accept **Toman**, including one decimal place for compatibility with pre-existing Rial prices. `25,000,000 Toman = 250,000,000 Rial` is converted exactly once when saving.
- Monetary values remain stored and exposed by the Django API in **Rial**, without changing order and inventory calculations. Never enter Rial in the Toman-labeled form.
- The optional compare-at price must be greater than the selling price. The variant's SKU remains unique.
- Only one image may be marked primary per product. To change the primary from an existing image to another, first uncheck the current primary and save; then mark the new image primary and save. This two-step workflow avoids the immediate database uniqueness constraint.
- Editing stock is **not** part of variant management. Use the protected InventoryBalance Admin so that stock adjustments are reflected in StockMovement. Never modify reserved stock by hand.
- Catalog operations require Django staff permissions; do not give product editors superuser or order/payment mutation rights by default.

Tests: `python manage.py test apps.catalog.tests_admin_forms --settings=config.settings.test`.
