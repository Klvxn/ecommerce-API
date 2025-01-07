# Generated by Django 5.0.6 on 2024-07-11 23:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0019_orderitem_created_orderitem_updated"),
    ]

    operations = [
        migrations.AlterField(
            model_name="orderitem",
            name="discounted_price",
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name="orderitem",
            name="discounted_shipping",
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name="orderitem",
            name="unit_price",
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
    ]