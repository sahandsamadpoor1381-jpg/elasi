from django.db import migrations, models

from apps.core.text import normalize_fa


def backfill_search_text(apps, schema_editor):
    """Fill the normalized search column for existing catalog rows."""

    Product = apps.get_model("catalog", "Product")

    updates = []

    for product in Product.objects.all().only(
        "id",
        "name",
        "short_description",
        "description",
        "slug",
    ):
        product.search_text = normalize_fa(
            " ".join(
                part
                for part in (
                    product.name,
                    product.short_description,
                    product.description,
                    product.slug,
                )
                if part
            ),
        )

        updates.append(product)

    if updates:
        Product.objects.bulk_update(updates, ["search_text"])


def clear_search_text(apps, schema_editor):
    """Reversible no-op: the column is dropped by the reverse migration."""


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0003_productimage_unique_primary_image_per_product"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="search_text",
            field=models.TextField(
                blank=True,
                default="",
                editable=False,
            ),
        ),
        migrations.RunPython(
            backfill_search_text,
            clear_search_text,
        ),
    ]
