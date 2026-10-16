from django.core.exceptions import ObjectDoesNotExist
from django.db import models


class Category(models.Model):
    name = models.CharField(
        max_length=120,
        unique=True,
    )

    slug = models.SlugField(
        max_length=140,
        unique=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    sort_order = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        ordering = ("sort_order", "name")
        verbose_name_plural = "Categories"

    def __str__(self) -> str:
        return self.name


class Collection(models.Model):
    name = models.CharField(
        max_length=120,
        unique=True,
    )

    slug = models.SlugField(
        max_length=140,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    class Gender(models.TextChoices):
        WOMEN = "women", "Women"
        MEN = "men", "Men"
        UNISEX = "unisex", "Unisex"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    name = models.CharField(
        max_length=180,
    )

    slug = models.SlugField(
        max_length=200,
        unique=True,
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )

    collections = models.ManyToManyField(
        Collection,
        related_name="products",
        blank=True,
    )

    short_description = models.CharField(
        max_length=300,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        default=Gender.UNISEX,
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    allow_custom_size = models.BooleanField(
        default=False,
    )

    is_featured = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self) -> str:
        return self.name


class ProductVariant(models.Model):
    class Material(models.TextChoices):
        GOLD = "gold", "Gold"
        SILVER = "silver", "Silver"

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
    )

    sku = models.CharField(
        max_length=80,
        unique=True,
    )

    material = models.CharField(
        max_length=10,
        choices=Material.choices,
    )

    karat = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    purity = models.CharField(
        max_length=20,
        blank=True,
    )

    size = models.CharField(
        max_length=50,
        blank=True,
    )

    weight_grams = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
    )

    price_rial = models.PositiveBigIntegerField()

    compare_at_price_rial = models.PositiveBigIntegerField(
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def get_available(self) -> int:
        """Available-to-sell units for this variant.

        Inactive variants are not sellable, so their availability is
        reported as 0 (previously the raw on_hand-reserved number was
        shown even for inactive variants, which was misleading).
        """
        if not self.is_active:
            return 0

        try:
            return max(0, self.inventory.available)
        except ObjectDoesNotExist:
            return 0

    def __str__(self) -> str:
        return f"{self.product.name} - {self.sku}"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )

    image = models.ImageField(
        upload_to="products/%Y/%m/",
    )

    alt_text = models.CharField(
        max_length=180,
        blank=True,
    )

    sort_order = models.PositiveIntegerField(
        default=0,
    )

    is_primary = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ("sort_order", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("product",),
                condition=models.Q(is_primary=True),
                name="unique_primary_image_per_product",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} image"