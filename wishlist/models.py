from django.contrib.auth import get_user_model
from django.db import models
from django.shortcuts import reverse
from django.utils.crypto import secrets

from catalogue.abstract import BaseModel
from catalogue.models import Product

# Create your models here.
User = get_user_model()


class Wishlist(BaseModel):
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

    class Meta(BaseModel.Meta):
        app_label = "catalogue"
        unique_together = ("name", "owner")

    @property
    def is_private(self):
        return self.audience == self.PRIVATE

    def __str__(self):
        return f"{self.name} Wishlist"

    def save(self, *args, **kwargs):
        if self.audience == self.SHARED:
            if not self.sharing_token:
                self.sharing_token = secrets.token_urlsafe(32)
        else:
            self.sharing_token = None
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("wishlist_detail", args=[self.id])

    def get_sharing_url(self):
        if self.audience == self.SHARED and self.sharing_token:
            return reverse("shared", args=[self.sharing_token])
        return None

    def add(self, product):
        item, created = self.items.get_or_create(product=product)
        return item if created else None

    def remove(self, product):
        self.items.filter(product=product).delete()

    @property
    def items_count(self):
        return self.items.count()


class WishlistItem(BaseModel):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product.name if self.product else "Deleted Product"

    class Meta:
        app_label = "catalogue"
        unique_together = ("wishlist", "product")
