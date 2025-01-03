# Generated by Django 5.0.6 on 2024-06-26 16:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0051_alter_wishlistitem_product"),
        ("orders", "0014_alter_orderitem_order"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="offer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="catalogue.offer",
            ),
        ),
    ]
