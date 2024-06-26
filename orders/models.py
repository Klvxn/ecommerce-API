from decimal import Decimal as D
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import models

from catalogue.models import Product
from catalogue.vouchers.models import Voucher, Offer
from customers.models import Address


# Create your models here.
User = get_user_model()


class Order(models.Model):
    """
    Represents a customer's order, containing order items, associated customer, and status.
    """
    class OrderStatus(models.TextChoices):
        PAID = "paid"
        AWAITING_PAYMENT = "awaiting_payment"
        DELIVERED = "delivered"

    id = models.UUIDField(primary_key=True, default=uuid4)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    offer = models.ForeignKey(
        "catalogue.Offer", on_delete=models.SET_NULL, null=True, blank=True
    )
    address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        verbose_name="Shipping address",
        null=True
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(
        choices=OrderStatus.choices,
        default=OrderStatus.AWAITING_PAYMENT,
        max_length=16,
    )

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return str(self.id)

    def redeem_order_discount(self, voucher_code):
        # Order offers are only redeemable via voucher codes.
        voucher = Voucher.objects.filter(code=voucher_code).first()
        if not (voucher and voucher.is_valid()):
            return None
        self.offer = voucher.offer
        self.save()
        return self.offer

    def total_shipping_fee(self):
        """
        Calculates the total shipping fee for the order.

        Returns:
            Decimal: The total shipping fee.
        """
        total_shipping = sum(items.shipping_fee for items in self.items.all())
        if self.offer and self.offer.is_free_shipping:
            total_shipping = self.offer.apply_discount(total_shipping)
        return total_shipping

    def total_cost(self):
        """
        Calculates the total cost of the order, including discounts and shipping.

        Returns:
            Decimal: The total cost of the order.
        """
        order_cost = sum(items.calculate_subtotal() for items in self.items.all())
        if self.offer and not self.offer.is_free_shipping:
            order_cost = self.offer.apply_discount(order_cost)
        total_cost = order_cost + self.total_shipping_fee()
        return total_cost

    def update_stock(self):
        for item in self.items.all().select_related('product'):
            item.product.in_stock -= item.quantity
            item.product.quantity_sold += item.quantity
            item.product.save()
            self.customer.total_items_bought += item.quantity
            if item.product not in self.customer.products_bought.all():
                self.customer.products_bought.add(item.product)
            self.customer.save()


class OrderItem(models.Model):
    """Represents an individual item within an order."""
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=D(0.00), blank=True
    )
    offer = models.ForeignKey(
        "catalogue.Offer", on_delete=models.SET_NULL, null=True, blank=True
    )
    quantity = models.PositiveIntegerField(default=1)
    shipping_fee = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"Item {self.id} in Order {self.order}"

    def calculate_subtotal(self):
        """
        Calculates the total cost for this order item.

        Returns:
            Decimal: The total cost of the item.
        """
        return (
            self.cost_at_original_price()
            if not self.discounted_price
            else self.cost_at_discounted_price()
        )
    
    def cost_at_discounted_price(self):
        """
        Calculates the total cost for this order item at the discounted price.

        Returns:
            Decimal: The total cost at the discounted price.
        """
        return self.discounted_price * self.quantity

    def cost_at_original_price(self):
        """
        Calculates the total cost for this order item at the original product's price.

        Returns:
            Decimal: The total cost at the original price.
        """
        return self.unit_price * self.quantity
    
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
        