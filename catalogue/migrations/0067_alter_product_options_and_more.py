# Generated by Django 5.0.6 on 2024-07-04 11:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0066_alter_offer_eligible_products_alter_voucher_offer"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="product",
            options={"ordering": ["-quantity_sold", "-rating"]},
        ),
        migrations.AddField(
            model_name="productattributevalue",
            name="price_increment",
            field=models.DecimalField(
                blank=2, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AlterField(
            model_name="offer",
            name="eligible_products",
            field=models.ManyToManyField(blank=True, to="catalogue.product"),
        ),
        migrations.AlterField(
            model_name="productattributevalue",
            name="attribute",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="value_set",
                to="catalogue.productattribute",
            ),
        ),
    ]
