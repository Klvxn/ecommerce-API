# Generated by Django 4.2 on 2024-06-11 19:24

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0025_discount_discount_type_alter_discount_code_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="discount",
            name="minimum_order_value",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AlterField(
            model_name="discount",
            name="discount_percentage",
            field=models.DecimalField(decimal_places=2, max_digits=5),
        ),
        migrations.AlterField(
            model_name="discount",
            name="discount_type",
            field=models.CharField(
                choices=[
                    ("order_discount", "Order discount"),
                    ("product_discount", "Product discount"),
                ],
                default="product_discount",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="shipping_fee",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=6, null=True
            ),
        ),
    ]
