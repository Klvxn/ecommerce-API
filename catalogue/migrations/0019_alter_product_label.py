# Generated by Django 4.1.2 on 2023-04-09 19:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0018_alter_product_label_alter_review_image_url"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="label",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
