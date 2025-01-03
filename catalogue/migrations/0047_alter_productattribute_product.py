# Generated by Django 5.0.6 on 2024-06-25 19:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0046_remove_product_attributes_productattribute_product"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productattribute",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attributes",
                to="catalogue.product",
            ),
        ),
    ]
