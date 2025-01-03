# Generated by Django 5.0.6 on 2024-06-25 19:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0043_review_sentiment_review_sentiment_score"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="product",
            name="attributes",
        ),
        migrations.AddField(
            model_name="productattribute",
            name="product",
            field=models.ForeignKey(
                default=3,
                on_delete=django.db.models.deletion.CASCADE,
                to="catalogue.product",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="productattribute",
            name="name",
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name="productattribute",
            name="value",
            field=models.CharField(max_length=100),
        ),
    ]
