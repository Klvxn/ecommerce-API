# Generated by Django 5.0.6 on 2024-06-25 15:59

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0042_remove_product_vendor_product_store"),
    ]

    operations = [
        migrations.AddField(
            model_name="review",
            name="sentiment",
            field=models.CharField(
                choices=[
                    ("POSITIVE", "Positive sentiment"),
                    ("Neutral", "Neutral sentiment"),
                    ("Negative", "Negative sentiment"),
                ],
                max_length=50,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="review",
            name="sentiment_score",
            field=models.FloatField(null=True),
        ),
    ]
