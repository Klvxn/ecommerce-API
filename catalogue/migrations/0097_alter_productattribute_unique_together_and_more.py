# Generated by Django 5.0.6 on 2025-03-05 20:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("catalogue", "0096_alter_productattribute_unique_together_and_more"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="productattribute",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="variantattribute",
            unique_together=set(),
        ),
    ]
