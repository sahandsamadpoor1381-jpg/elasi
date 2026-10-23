"""Shared storefront content controlled by the merchant."""

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Q


class HomePageContent(models.Model):
    """Single editable homepage; drafts are never exposed on the public API."""

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    is_published = models.BooleanField(default=False, verbose_name="منتشر شده")
    hero_eyebrow = models.CharField(max_length=80, default="ELASI JEWELRY", verbose_name="متن بالای Hero")
    hero_heading = models.CharField(max_length=180, default="زیبایی‌ای که\nبا شما ماندگار\nمی‌شود.", verbose_name="عنوان Hero")
    hero_description = models.TextField(
        max_length=500,
        default="مجموعه‌ای از جواهرات طلا و نقره با نگاهی مدرن، ظریف و ماندگار؛ برای انتخاب‌هایی که بخشی از استایل شخصی شما می‌شوند.",
        verbose_name="توضیح Hero",
    )
    hero_image = models.ImageField(
        upload_to="site/home/",
        blank=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
        verbose_name="تصویر Hero",
    )
    hero_image_alt = models.CharField(max_length=180, blank=True, verbose_name="توضیح تصویر برای دسترس‌پذیری")
    hero_primary_label = models.CharField(max_length=60, default="مشاهده مجموعه", verbose_name="دکمه فروشگاه")
    hero_secondary_label = models.CharField(max_length=60, default="داستان ELASI", verbose_name="دکمه درباره ما")
    story_heading = models.CharField(
        max_length=180,
        default="جواهر، فقط یک انتخاب نیست؛ بخشی از روایت شماست.",
        verbose_name="عنوان داستان برند",
    )
    story_description = models.TextField(
        max_length=600,
        default="ELASI با تمرکز بر فرم‌های ظریف، ترکیب‌های ماندگار و زیبایی بدون اغراق شکل گرفته است. هدف ما ساخت تجربه‌ای است که در آن انتخاب جواهر، ساده، شخصی و نزدیک به سبک زندگی شما باشد.",
        verbose_name="متن داستان برند",
    )
    closing_heading = models.CharField(
        max_length=180,
        default="انتخابی که به سبک شما نزدیک‌تر است",
        verbose_name="عنوان دعوت پایانی",
    )
    closing_description = models.TextField(
        max_length=500,
        default="مجموعه ELASI را ببینید و میان فرم‌ها، متریال‌ها و جزئیات مختلف، انتخاب مناسب خودتان را پیدا کنید.",
        verbose_name="توضیح دعوت پایانی",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "محتوای صفحه اصلی"
        verbose_name_plural = "محتوای صفحه اصلی"
        constraints = [
            models.CheckConstraint(condition=Q(pk=1), name="core_homepage_content_singleton"),
        ]

    def clean(self):
        super().clean()
        if self.hero_image:
            if not self.hero_image_alt.strip():
                raise ValidationError({"hero_image_alt": "برای تصویر Hero توضیح کوتاه ثبت کنید."})
            if self.hero_image.size > 5 * 1024 * 1024:
                raise ValidationError({"hero_image": "اندازه تصویر نباید بیشتر از ۵ مگابایت باشد."})

    def __str__(self):
        return "محتوای صفحه اصلی ELASI"
