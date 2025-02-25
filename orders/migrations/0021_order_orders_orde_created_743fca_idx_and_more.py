# Generated by Django 5.0.6 on 2025-01-05 15:52

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("customers", "0012_rename_total_items_bought_customer_products_bought_count"),
        ("orders", "0020_alter_orderitem_discounted_price_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["-created"], name="orders_orde_created_743fca_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(fields=["status"], name="orders_orde_status_c6dd84_idx"),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["customer", "-created"], name="orders_orde_custome_c13716_idx"
            ),
        ),
    ]
