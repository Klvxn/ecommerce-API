# Generated by Django 5.0.6 on 2024-06-18 12:06

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0036_remove_product_discount_redeemedvoucher_voucher"),
        ("orders", "0010_alter_order_status_alter_orderitem_discounted_price_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="discount",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="catalogue.discount",
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid4, primary_key=True, serialize=False
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("paid", "Paid"),
                    ("awaiting_payment", "Awaiting Payment"),
                    ("delivered", "Delivered"),
                ],
                default="awaiting_payment",
                max_length=16,
            ),
        ),
        migrations.AlterField(
            model_name="orderitem",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="catalogue.product"
            ),
        ),
    ]
