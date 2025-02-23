# Generated by Django 5.0.6 on 2025-02-23 08:00

import django.db.models.deletion
import django.db.models.expressions
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("discount", "0003_alter_offercondition_unique_together"),
        ("orders", "0026_rename_offer_order_applied_offer_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="applied_offer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="order_offer",
                to="discount.offer",
            ),
        ),
    ]
