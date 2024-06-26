# Generated by Django 4.2 on 2024-06-10 09:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0023_remove_discount_product_discount_created_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="discount",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="catalogue.discount",
            ),
        ),
    ]
