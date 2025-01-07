# Generated by Django 5.0.6 on 2024-07-11 15:34

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0018_alter_orderitem_unit_price"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderitem",
            name="created",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="orderitem",
            name="updated",
            field=models.DateTimeField(auto_now=True),
        ),
    ]