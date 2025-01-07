# Generated by Django 5.0.6 on 2024-06-27 21:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0059_remove_product_product_attribute_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="product",
            name="attributes",
        ),
        migrations.AddField(
            model_name="productattribute",
            name="product",
            field=models.ForeignKey(
                default=2,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attributes",
                to="catalogue.product",
            ),
            preserve_default=False,
        ),
    ]