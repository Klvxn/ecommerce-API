# Generated by Django 4.1.2 on 2023-04-10 09:24

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("vendors", "0004_alter_vendor_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="vendor",
            name="is_staff",
            field=models.BooleanField(default=True),
        ),
    ]
