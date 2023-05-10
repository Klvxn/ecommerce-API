from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import models

from customers.models import Address
from products.models import Product


# Create your models here.
User = get_user_model()


class Order(models.Model):

    class OrderStatus(models.TextChoices):
        PAID = "paid"
        UNPAID = "unpaid"
        DELIVERED = "delivered"

    id = models.UUIDField("Order Id", primary_key=True, default=uuid4, editable=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        verbose_name="Shipping address",
        null=True
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(
        "Order status",
        choices=OrderStatus.choices,
        default=OrderStatus.UNPAID,
        max_length=10,
    )

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return str(self.id)

    def get_total_shipping_fee(self):
        return sum(items.shipping_fee for items in self.order_items.all())

    def get_total_cost(self):
        return sum(items.get_cost() for items in self.order_items.all())  + self.get_total_shipping_fee()


class OrderItem(models.Model):

    order = models.ForeignKey(Order, related_name="order_items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="items", on_delete=models.CASCADE)
    cost_per_item = models.DecimalField(max_digits=6, decimal_places=2, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    shipping_fee = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        if not self.cost_per_item or self.cost_per_item != self.product.price:
            self.cost_per_item = self.product.price
        return super().save(*args, **kwargs)

    def get_cost(self):
        return self.cost_per_item * self.quantity
