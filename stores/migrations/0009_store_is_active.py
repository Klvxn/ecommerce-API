# Generated by Django 5.0.6 on 2025-03-16 20:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stores", "0008_store_is_verified"),
    ]

    operations = [
        migrations.AddField(
            model_name="store",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
