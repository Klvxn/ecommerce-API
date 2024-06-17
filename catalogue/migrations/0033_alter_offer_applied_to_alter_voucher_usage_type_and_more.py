# Generated by Django 4.2 on 2024-06-17 11:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalogue", "0032_alter_offer_applied_to_alter_offer_eligible_products"),
    ]

    operations = [
        migrations.AlterField(
            model_name="offer",
            name="applied_to",
            field=models.CharField(
                choices=[
                    ("Vouchers", "Accessible after a customer enters the vouchers code"),
                    ("All users", "The offer is applicable to all customers"),
                    (
                        "First time buyers",
                        "first time buyers only can redeem this offer",
                    ),
                ],
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="vouchers",
            name="usage_type",
            field=models.CharField(
                choices=[
                    ("single", "Can only be used once"),
                    ("multiple", "Can be used multiple number of times"),
                    ("once per customer", "Can be used once for every customer"),
                ],
                default="once per customer",
                max_length=50,
            ),
        ),
        migrations.CreateModel(
            name="RedeemedVoucher",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date_redeemed", models.DateTimeField(auto_now_add=True)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "vouchers",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="catalogue.vouchers",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="vouchers",
            name="redeemed_by",
            field=models.ManyToManyField(
                through="catalogue.RedeemedVoucher", to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
