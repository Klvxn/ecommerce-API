# Generated by Django 5.0.6 on 2024-06-18 12:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0003_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="transaction_id",
            field=models.CharField(blank=True, max_length=255, unique=True),
        ),
    ]