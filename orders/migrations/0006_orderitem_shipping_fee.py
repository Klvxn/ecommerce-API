# Generated by Django 4.2 on 2023-05-10 16:33

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0005_alter_order_address"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderitem",
            name="shipping_fee",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=6),
            preserve_default=False,
        ),
    ]