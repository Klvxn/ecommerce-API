# Generated by Django 4.1.2 on 2023-04-09 19:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0016_alter_product_label_alter_review_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="review",
            name="image_url",
            field=models.URLField(default="product_review_default_image_url.png"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="review",
            name="updated",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
