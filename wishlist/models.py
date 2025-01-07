from django.contrib.auth import get_user_model
from django.db import models
from django.shortcuts import reverse
from django.utils.crypto import secrets

from catalogue.models import Timestamp, Product


# Create your models here.
User = get_user_model()


class Wishlist(Timestamp):
    PUBLIC = "public"
    PRIVATE = "private"
    SHARED = "shared"

    WISHLIST_AUDIENCE = (
        (PUBLIC, "Anyone can view this wishlist"),
        (PRIVATE, "Only you can view your wishlist"),
        (SHARED, "Only users with the url can view the wishlist"),
    )
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    audience = models.CharField(max_length=50, choices=WISHLIST_AUDIENCE, default=PRIVATE)
    note = models.TextField(null=True, blank=True)
    sharing_token = models.CharField(max_length=50, unique=True, null=True, blank=True)

    class Meta:
        app_label = "catalogue"
        unique_together = ("name", "owner")

    @property
    def is_private(self):
        return self.audience == self.PRIVATE

    def __str__(self):
        return f"{self.name} Wishlist"

    def save(self, *args, **kwargs):
        if self.audience == "shared":
            self.sharing_token = secrets.token_urlsafe(32)
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("wishlist_detail", args=[self.id])

    def get_sharing_url(self):
        if self.audience == "shared" and self.sharing_token:
            return reverse("shared", [self.sharing_token])

    def get_public_url(self):
        if not self.is_private:
            return reverse("public_wishlist", args=[self.id])

    def add(self, product):
        if self.items and self.items.filter(product=product).exists():
            return
        return self.items.create(product=product)

    def remove(self, product):
        if self.items and self.items.filter(product=product).exists():
            self.items.filter(product=product).delete()
        return


class WishlistItem(Timestamp):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product.name

    class Meta:
        app_label = "catalogue"
        unique_together = ("wishlist", "product")
