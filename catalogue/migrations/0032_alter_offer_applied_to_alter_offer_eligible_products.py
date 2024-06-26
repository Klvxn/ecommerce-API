# Generated by Django 4.2 on 2024-06-15 16:46

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0031_alter_offer_eligible_products_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="offer",
            name="applied_to",
            field=models.CharField(
                choices=[
                    ("vouchers", "Accessible after a customer enters the vouchers code"),
                    ("all users", "The offer is applicable to all customers"),
                    (
                        "First time buyers",
                        "Only a certain type of customer is this offer applicable to .e.g. first time buyers",
                    ),
                ],
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="offer",
            name="eligible_products",
            field=models.ManyToManyField(blank=True, to="catalogue.product"),
        ),
    ]
