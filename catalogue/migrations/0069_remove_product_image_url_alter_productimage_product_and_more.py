# Generated by Django 5.0.6 on 2024-07-11 10:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0068_remove_productattributevalue_price_increment_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="product",
            name="image_url",
        ),
        migrations.AlterField(
            model_name="productimage",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="image_set",
                to="catalogue.product",
            ),
        ),
        migrations.AlterField(
            model_name="voucher",
            name="code",
            field=models.CharField(db_index=True, max_length=50, unique=True),
        ),
    ]
