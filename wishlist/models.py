from django.db import models
from django.contrib.auth import get_user_model
from django.shortcuts import reverse

from catalogue.models import BaseModel, Product


# Create your models here.
User = get_user_model()

class Wishlist(BaseModel):
    PUBLIC = "public"
    PRIVATE = "private"

    WISHLIST_AUDIENCE = (
        (PUBLIC, "Anyone can view this wishlist"),
        (PRIVATE, "Only you can view your wishlist")
    )
    name = models.CharField(max_length=50)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    audience = models.CharField(max_length=50, choices=WISHLIST_AUDIENCE, default=PRIVATE)
    note = models.TextField(null=True, blank=True)

    class Meta:
        app_label = "catalogue"
        unique_together = ("name", "owner")

    def __str__(self):
        return f"{self.name} Wishlist"

    def add_to_wishlist(self, product):
        if self.items and self.items.filter(product=product).exists():
            return
        return self.items.create(product=product)

    def remove_(self, product):
        if self.items and self.items.filter(product=product).exists():
            self.items.filter(product=product).delete()
        return

    @property
    def is_private(self):
        return self.audience == self.PRIVATE

    def get_absolute_url(self):
        return reverse("wishlist_detail", self.id)

    def get_public_url(self):
        if not self.is_private:
            return reverse("public_wishlist", self.id)

class WishlistItem(BaseModel):
    wishlist = models.ForeignKey(
        Wishlist, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.product.name

    class Meta:
        app_label = "catalogue"
        unique_together = ("wishlist", "product")
