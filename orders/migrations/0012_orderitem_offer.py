# Generated by Django 5.0.6 on 2024-06-19 01:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0038_rename_max_usage_voucher_max_usage_limit_and_more"),
        ("orders", "0011_alter_order_discount_alter_order_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderitem",
            name="offer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="catalogue.offer",
            ),
        ),
    ]