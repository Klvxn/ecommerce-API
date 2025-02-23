# Generated by Django 5.0.6 on 2025-01-05 15:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogue", "0072_rename_review_review_review_text_and_more"),
        ("stores", "0004_store_address"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductMedia",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("file", models.FileField(upload_to="products/%Y/%m/")),
                (
                    "is_primary",
                    models.BooleanField(
                        default=False, help_text="Set as primary media for product"
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "product media",
            },
        ),
        migrations.RemoveField(
            model_name="productimage",
            name="product",
        ),
        migrations.AlterUniqueTogether(
            name="productattributevalue",
            unique_together={("attribute", "value")},
        ),
        migrations.RemoveField(
            model_name="reviewimage",
            name="created",
        ),
        migrations.RemoveField(
            model_name="reviewimage",
            name="image_url",
        ),
        migrations.RemoveField(
            model_name="reviewimage",
            name="title",
        ),
        migrations.AddField(
            model_name="productattributevalue",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="productattributevalue",
            name="price_adjustment",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name="wishlist",
            name="sharing_token",
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name="product",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.DO_NOTHING, to="catalogue.category"
            ),
        ),
        migrations.AlterField(
            model_name="reviewimage",
            name="review",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="images",
                to="catalogue.review",
            ),
        ),
        migrations.AlterField(
            model_name="voucher",
            name="name",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="wishlist",
            name="audience",
            field=models.CharField(
                choices=[
                    ("public", "Anyone can view this wishlist"),
                    ("private", "Only you can view your wishlist"),
                    ("shared", "Only users with the url can view the wishlist"),
                ],
                default="private",
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="wishlist",
            name="name",
            field=models.CharField(max_length=100),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["category", "available"], name="catalogue_p_categor_9848b4_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="productattributevalue",
            index=models.Index(
                fields=["attribute", "is_active"], name="catalogue_p_attribu_475448_idx"
            ),
        ),
        migrations.AddField(
            model_name="productmedia",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="media",
                to="catalogue.product",
            ),
        ),
        migrations.DeleteModel(
            name="ProductImage",
        ),
    ]
