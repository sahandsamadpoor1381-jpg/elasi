from django.core.validators import FileExtensionValidator
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="HomePageContent",
            fields=[
                ("id", models.PositiveSmallIntegerField(default=1, editable=False, primary_key=True, serialize=False)),
                ("is_published", models.BooleanField(default=False, verbose_name="منتشر شده")),
                ("hero_eyebrow", models.CharField(default="ELASI JEWELRY", max_length=80, verbose_name="متن بالای Hero")),
                ("hero_heading", models.CharField(default="زیبایی‌ای که\nبا شما ماندگار\nمی‌شود.", max_length=180, verbose_name="عنوان Hero")),
                ("hero_description", models.TextField(default="مجموعه‌ای از جواهرات طلا و نقره با نگاهی مدرن، ظریف و ماندگار؛ برای انتخاب‌هایی که بخشی از استایل شخصی شما می‌شوند.", max_length=500, verbose_name="توضیح Hero")),
                ("hero_image", models.ImageField(blank=True, upload_to="site/home/", validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])], verbose_name="تصویر Hero")),
                ("hero_image_alt", models.CharField(blank=True, max_length=180, verbose_name="توضیح تصویر برای دسترس‌پذیری")),
                ("hero_primary_label", models.CharField(default="مشاهده مجموعه", max_length=60, verbose_name="دکمه فروشگاه")),
                ("hero_secondary_label", models.CharField(default="داستان ELASI", max_length=60, verbose_name="دکمه درباره ما")),
                ("story_heading", models.CharField(default="جواهر، فقط یک انتخاب نیست؛ بخشی از روایت شماست.", max_length=180, verbose_name="عنوان داستان برند")),
                ("story_description", models.TextField(default="ELASI با تمرکز بر فرم‌های ظریف، ترکیب‌های ماندگار و زیبایی بدون اغراق شکل گرفته است. هدف ما ساخت تجربه‌ای است که در آن انتخاب جواهر، ساده، شخصی و نزدیک به سبک زندگی شما باشد.", max_length=600, verbose_name="متن داستان برند")),
                ("closing_heading", models.CharField(default="انتخابی که به سبک شما نزدیک‌تر است", max_length=180, verbose_name="عنوان دعوت پایانی")),
                ("closing_description", models.TextField(default="مجموعه ELASI را ببینید و میان فرم‌ها، متریال‌ها و جزئیات مختلف، انتخاب مناسب خودتان را پیدا کنید.", max_length=500, verbose_name="توضیح دعوت پایانی")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "محتوای صفحه اصلی",
                "verbose_name_plural": "محتوای صفحه اصلی",
                "constraints": [models.CheckConstraint(condition=Q(pk=1), name="core_homepage_content_singleton")],
            },
        ),
    ]
