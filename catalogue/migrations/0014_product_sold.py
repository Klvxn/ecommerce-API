# Generated by Django 4.1.2 on 2022-11-19 11:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalogue", "0013_alter_review_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="sold",
            field=models.PositiveIntegerField(default=0, verbose_name="Products sold"),
        ),
    ]