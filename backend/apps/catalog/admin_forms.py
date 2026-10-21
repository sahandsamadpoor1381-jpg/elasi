"""Merchant-safe catalog forms.

The public API and database store Rial, while merchants enter Toman.
Convert exactly once in the admin form. The model and API contracts remain
unchanged, so existing order-price snapshots remain authoritative.
"""

from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from .models import ProductImage, ProductVariant


RIAL_PER_TOMAN = Decimal("10")
MAX_RIAL_BIGINT = Decimal(2**63 - 1)


class ProductVariantAdminForm(forms.ModelForm):
    price_toman = forms.DecimalField(
        label="قیمت فروش (تومان)",
        max_digits=19,
        decimal_places=1,
        min_value=Decimal("0.1"),
        help_text="مبلغ را به تومان وارد کنید؛ سیستم آن را دقیقاً یک‌بار به ریال تبدیل می‌کند.",
    )
    compare_at_price_toman = forms.DecimalField(
        label="قیمت قبل از تخفیف (تومان)",
        max_digits=19,
        decimal_places=1,
        min_value=Decimal("0.1"),
        required=False,
        help_text="اختیاری؛ در صورت ورود، باید از قیمت فروش بیشتر باشد.",
    )

    class Meta:
        model = ProductVariant
        exclude = ("price_rial", "compare_at_price_rial")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial.setdefault(
                "price_toman", Decimal(self.instance.price_rial) / RIAL_PER_TOMAN
            )
            if self.instance.compare_at_price_rial is not None:
                self.initial.setdefault(
                    "compare_at_price_toman",
                    Decimal(self.instance.compare_at_price_rial) / RIAL_PER_TOMAN,
                )

    def clean(self):
        data = super().clean()
        price = data.get("price_toman")
        compare_at = data.get("compare_at_price_toman")
        if price is not None and price * RIAL_PER_TOMAN > MAX_RIAL_BIGINT:
            self.add_error("price_toman", "قیمت از محدوده مجاز ذخیره‌سازی بیشتر است.")
        if compare_at is not None and compare_at * RIAL_PER_TOMAN > MAX_RIAL_BIGINT:
            self.add_error("compare_at_price_toman", "قیمت از محدوده مجاز ذخیره‌سازی بیشتر است.")
        if price is not None and compare_at is not None and compare_at <= price:
            self.add_error("compare_at_price_toman", "قیمت قبل از تخفیف باید از قیمت فروش بیشتر باشد.")
        return data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # DecimalField(decimal_places=1) guarantees an integral Rial amount.
        instance.price_rial = int(self.cleaned_data["price_toman"] * RIAL_PER_TOMAN)
        compare_at = self.cleaned_data.get("compare_at_price_toman")
        instance.compare_at_price_rial = (
            int(compare_at * RIAL_PER_TOMAN) if compare_at is not None else None
        )
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ProductImageInlineFormSet(BaseInlineFormSet):
    """Report duplicate primary images in the form, before the DB constraint."""

    def clean(self):
        super().clean()
        if any(self.errors):
            return
        primary_count = sum(
            bool(form.cleaned_data.get("is_primary"))
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False)
        )
        if primary_count > 1:
            raise ValidationError("برای هر محصول فقط یک تصویر اصلی انتخاب کنید.")

        # The DB constraint is immediate. Replacing the current primary in
        # one inline submission can fail depending on save order. Require a
        # safe two-step change rather than an unhandled IntegrityError.
        current_primary_id = (
            ProductImage.objects.filter(product=self.instance, is_primary=True)
            .values_list("pk", flat=True)
            .first()
            if self.instance.pk else None
        )
        if current_primary_id is not None and primary_count:
            selected = next(
                (form.instance.pk for form in self.forms
                 if form.cleaned_data and not form.cleaned_data.get("DELETE", False)
                 and form.cleaned_data.get("is_primary")),
                None,
            )
            if selected != current_primary_id:
                raise ValidationError(
                    "برای تغییر تصویر اصلی، ابتدا تیک تصویر اصلی فعلی را بردارید "
                    "و ذخیره کنید؛ سپس تصویر جدید را اصلی کنید."
                )


class ProductImageAdminForm(forms.ModelForm):
    """Guard standalone image edits against an already selected primary."""

    class Meta:
        model = ProductImage
        fields = "__all__"

    def clean(self):
        data = super().clean()
        product = data.get("product")
        if product is not None and data.get("is_primary"):
            existing_primary = ProductImage.objects.filter(
                product=product, is_primary=True
            )
            if self.instance.pk:
                existing_primary = existing_primary.exclude(pk=self.instance.pk)
            if existing_primary.exists():
                self.add_error(
                    "is_primary",
                    "این محصول تصویر اصلی دارد؛ ابتدا تصویر قبلی را غیراصلی کنید.",
                )
        return data
