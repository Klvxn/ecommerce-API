# Generated by Django 5.0.6 on 2024-07-03 19:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0017_remove_order_offer_orderitem_discounted_shipping_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="orderitem",
            name="unit_price",
            field=models.DecimalField(decimal_places=2, editable=False, max_digits=10),
        ),
    ]
