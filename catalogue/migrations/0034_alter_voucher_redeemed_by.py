# Generated by Django 4.2 on 2024-06-17 11:09

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalogue", "0033_alter_offer_applied_to_alter_voucher_usage_type_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="vouchers",
            name="redeemed_by",
            field=models.ManyToManyField(
                blank=True,
                through="catalogue.RedeemedVoucher",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
