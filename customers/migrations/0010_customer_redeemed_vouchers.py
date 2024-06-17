# Generated by Django 4.2 on 2024-06-17 11:17

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0035_remove_voucher_redeemed_by_and_more"),
        ("customers", "0009_alter_customer_products_bought_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="redeemed_vouchers",
            field=models.ManyToManyField(
                blank=True, through="catalogue.RedeemedVoucher", to="catalogue.vouchers"
            ),
        ),
    ]
