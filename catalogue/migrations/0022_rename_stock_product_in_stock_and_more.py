# Generated by Django 4.2 on 2024-06-10 09:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalogue", "0021_product_shipping_fee"),
    ]

    operations = [
        migrations.RenameField(
            model_name="product",
            old_name="stock",
            new_name="in_stock",
        ),
        migrations.RenameField(
            model_name="product",
            old_name="sold",
            new_name="quantity_sold",
        ),
        migrations.CreateModel(
            name="Discount",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50)),
                ("code", models.CharField(max_length=10)),
                ("description", models.TextField()),
                ("discount_percentage", models.CharField(max_length=3)),
                ("active", models.BooleanField(default=False)),
                ("valid_from", models.DateTimeField()),
                ("valid_to", models.DateTimeField()),
                (
                    "owner",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="product_discount",
                        to="catalogue.product",
                    ),
                ),
            ],
        ),
    ]
