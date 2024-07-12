from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import models

from catalogue.models import BaseModel, Product
from catalogue.vouchers.models import Voucher, Offer
from customers.models import Address


# Create your models here.
User = get_user_model()


class Order(BaseModel):
    """
    Represents a customer's order, containing order items, associated customer, and status.
    """
    class OrderStatus(models.TextChoices):
        PAID = "paid"
        AWAITING_PAYMENT = "awaiting_payment"
        DELIVERED = "delivered"

    id = models.UUIDField(primary_key=True, default=uuid4)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        verbose_name="Shipping address",
        null=True
    )
    status = models.CharField(
        choices=OrderStatus.choices,
        default=OrderStatus.AWAITING_PAYMENT,
        max_length=16,
    )

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return str(self.id)

    @property
    def items_count(self):
        return sum(item.quantity for item in self.items.all())

    def redeem_voucher_offer(self, voucher_code):
        """
        Apply a voucher offer to the order items in an order

        This method checks each item in the order to see if the provided voucher code
        applies to any of the products in the order. If the voucher is valid and applicable,
        the discount is applied.

        Args:
            voucher_code (str): The code of the voucher to redeem

        Returns:
            offer (Offer or None): The offer applied to the order items if voucher is
            valid. None if the voucher is invalid
        """
        offer = None
        for item in self.items.all():
            # Fetch the voucher that matches the provided code and
            # is eligible for the product in the item
            voucher = Voucher.objects.filter(
                code=voucher_code.upper(), offer__eligible_products=item.product
            ).first()
            if not (voucher and voucher.is_valid()):
                return None
            # Get the offer associated with the voucher and apply the discounts
            offer = voucher.offer
            if offer.for_product:
                item.discounted_price = offer.apply_discount(item.unit_price)
            if offer.for_shipping:
                item.discounted_shipping = offer.apply_discount(item.shipping_fee)
            # Save the offer to the item
            item.offer = offer
            item.save()
        return offer

    def total_shipping_fee(self):
        """
        Calculates the total shipping fee for the order.

        Returns:
            Decimal: The total shipping fee.
        """
        total_shipping = sum(item.get_shipping() for item in self.items.all())
        return total_shipping

    def total_cost(self):
        """
        Calculates the total cost of the order, including discounts and shipping.

        Returns:
            Decimal: The total cost of the order.
        """
        order_cost = sum(items.calculate_subtotal() for items in self.items.all())
        total_cost = order_cost + self.total_shipping_fee()
        return total_cost


class OrderItem(BaseModel):
    """
    Represents an individual item within an order.
    """
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    selected_attrs = models.JSONField(null=True, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True
    )
    quantity = models.PositiveIntegerField(default=1)
    offer = models.ForeignKey(
        "catalogue.Offer", on_delete=models.SET_NULL, null=True, blank=True
    )
    shipping_fee = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    discounted_shipping = models.DecimalField(
        max_digits=10, decimal_places=2, null=True
    )

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

    def get_shipping(self):
        """
        Checks if an order item has a discounted shipping fee. Otherwise, it returns
        the regular shipping fee.

        Returns:
            Decimal: The applicable shipping fee for the order item.
        """
        return (
            self.discounted_shipping
            if self.discounted_shipping
            else self.shipping_fee
        )
    
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

            offer_id = 0
            discounted_price = discounted_shipping = None
            if discount:= item.get("discount"):
                offer_id = discount.get("offer_id")
                discounted_price = discount.get("discounted_price")
                discounted_shipping = discount.get("discounted_price")

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item.get("quantity"),
                unit_price=item.get("price"),
                discounted_price=discounted_price,
                discounted_shipping=discounted_shipping,
                offer_id=offer_id,
                shipping_fee=item.get("shipping"),
                selected_attrs=item.get("selected_attrs")
            )
