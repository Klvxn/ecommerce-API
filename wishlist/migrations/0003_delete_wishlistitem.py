# Generated by Django 5.0.6 on 2024-06-25 22:16

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("wishlist", "0002_alter_wishlistitem_wishlist_delete_wishlist"),
    ]

    operations = [
        migrations.DeleteModel(
            name="WishlistItem",
        ),
    ]