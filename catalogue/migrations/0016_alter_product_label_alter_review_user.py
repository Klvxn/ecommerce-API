# Generated by Django 4.1.2 on 2023-03-28 16:01

from django.conf import settings
from django.db import migrations, models
import catalogue.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalogue", "0015_alter_product_sold"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="label",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="review",
            name="user",
            field=models.ForeignKey(
                on_delete=models.SET(catalogue.models.get_sentinel_user),
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
