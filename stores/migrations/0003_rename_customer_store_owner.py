# Generated by Django 5.0.6 on 2024-06-25 16:01

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("stores", "0002_store_followers"),
    ]

    operations = [
        migrations.RenameField(
            model_name="store",
            old_name="customer",
            new_name="owner",
        ),
    ]