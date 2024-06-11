from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import models

from customers.models import Address
from products.models import Product, Discount


# Create your models here.
User = get_user_model()


class Order(models.Model):
    """
    Represents a customer's order, containing order details, associated customer, and status.
    """
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
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, null=True)
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

    def total_shipping_fee(self):
        """
        Calculates the total shipping fee for the order.

        Returns:
            Decimal: The total shipping fee.
        """
        return sum(items.shipping_fee for items in self.order_items.all())

    def total_cost(self):
        """
        Calculates the total cost of the order, including discounts and shipping.

        Returns:
            Decimal: The total cost of the order.
        """
        order_cost = sum(items.calculate_cost() for items in self.order_items.all())
        if self.discount:
            discounted_price = self.discount.apply_discount(order_cost)
            total_cost = discounted_price + self.total_shipping_fee()
        else:
            total_cost = order_cost + self.total_shipping_fee()
        return total_cost


class OrderItem(models.Model):
    """Represents an individual item within an order."""
    order = models.ForeignKey(Order, related_name="order_items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="items", on_delete=models.CASCADE)
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    shipping_fee = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return str(self.id)

    def calculate_cost(self):
        """
        Calculates the total cost for this order item.

        Returns:
            Decimal: The total cost of the item.
        """
        return self.unit_price * self.quantity if not self.discounted_price else self.cost_for_discounted_price()
    
    def cost_for_discounted_price(self):
        """
        Calculates the total cost for this order item with the discounted price.

        Returns:
            Decimal: The total cost with the discounted price.
        """
        return self.discounted_price * self.quantity
    
    @classmethod
    def create_from_cart(cls, order, user_cart):
        """
        Creates OrderItems from the items in the user's cart.

        Args:
            order (Order): The order to which the items should be added.
            user_cart (Cart): The user's cart containing items to be added to the order.
        
        Returns:
            None
        """
        for item in user_cart:
            product = Product.objects.get(name=item["product"])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item.get("quantity"),
                unit_price=item.get("price"),
                discounted_price=item.get("discounted_price"),
                shipping_fee=item.get("shipping_fee")
            )
        