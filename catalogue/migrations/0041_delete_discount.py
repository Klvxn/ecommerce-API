# Generated by Django 5.0.6 on 2024-06-19 20:49

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0040_productattribute_remove_product_attributes_and_more"),
        ("orders", "0013_remove_order_discount_and_more"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Discount",
        ),
    ]