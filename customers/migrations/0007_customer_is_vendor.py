# Generated by Django 4.1.2 on 2023-04-10 12:04

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("customers", "0006_alter_customer_date_of_birth"),
    ]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="is_vendor",
            field=models.BooleanField(default=False),
        ),
    ]