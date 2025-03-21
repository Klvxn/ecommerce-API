# Generated by Django 5.0.6 on 2025-03-07 20:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalogue", "0097_alter_productattribute_unique_together_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="productmedia",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="review",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="wishlist",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="wishlistitem",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterUniqueTogether(
            name="productattribute",
            unique_together={("product", "name")},
        ),
        migrations.AlterUniqueTogether(
            name="variantattribute",
            unique_together={("variant", "attribute")},
        ),
    ]
