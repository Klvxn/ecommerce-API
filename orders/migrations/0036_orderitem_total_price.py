# Generated by Django 5.0.6 on 2025-03-05 20:24

import django.db.models.expressions
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0035_remove_orderitem_discounted_price"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderitem",
            name="total_price",
            field=models.GeneratedField(
                db_persist=True,
                expression=django.db.models.expressions.CombinedExpression(
                    models.F("unit_price"), "*", models.F("quantity")
                ),
                output_field=models.DecimalField(decimal_places=2, max_digits=10),
            ),
        ),
    ]
