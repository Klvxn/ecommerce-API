from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import models

from catalogue.models import Timestamp, Product
from catalogue.vouchers.models import Voucher
from customers.models import Address


# Create your models here.
User = get_user_model()


class Order(Timestamp):
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
        Address, on_delete=models.SET_NULL, verbose_name="Shipping address", null=True
    )
    status = models.CharField(
        choices=OrderStatus.choices,
        default=OrderStatus.AWAITING_PAYMENT,
        max_length=16,
    )

    class Meta:
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["-created"]),
            models.Index(fields=["status"]),
            models.Index(fields=["customer", "-created"]),
        ]

    def __str__(self):
        return str(self.id)

    @property
    def items_count(self):
        return Order.objects.get(id=self.id).annotate(total_items=models.Sum("items__quantity"))

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

        items = self.items.select_related("product").all()
        product_ids = [item.product_id for item in items]
        voucher = (
            Voucher.objects.filter(
                code=voucher_code.upper(), offer__eligible_products__id__in=product_ids
            )
            .select_related("offer")
            .first()
        )

        if not (voucher and voucher.is_valid()):
            return None

        items_to_update = []
        offer = voucher.offer

        for item in items:
            if item.product_id in product_ids:
                if offer.for_product:
                    item.discounted_price = offer.apply_discount(item.unit_price)
                if offer.for_shipping:
                    item.discounted_shipping = offer.apply_discount(item.shipping_fee)
                item.offer = offer
                items_to_update.append(item)

        OrderItem.objects.bulk_update(
            items_to_update, ["discounted_price", "discounted_shipping", "offer"]
        )

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


class OrderItem(Timestamp):
    """
    Represents an individual item within an order.
    """

    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    selected_attrs = models.JSONField(null=True, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    quantity = models.PositiveIntegerField(default=1)
    offer = models.ForeignKey("catalogue.Offer", on_delete=models.SET_NULL, null=True, blank=True)
    shipping_fee = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    discounted_shipping = models.DecimalField(max_digits=10, decimal_places=2, null=True)

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
        return self.discounted_shipping if self.discounted_shipping else self.shipping_fee

    @classmethod
    def create_from_cart(cls, order, user_cart):
        """
        Creates OrderItems from the items in the user's cart.

        Args:
            order (Order): The order to which the items should be added.
            user_cart (Cart): The user's cart containing items to be added to the order.

        Returns:
            int: The number of records that was created
        """

        product_names = {item["product"] for item in user_cart}
        products = {prod.name: prod for prod in Product.objects.filter(name__in=product_names)}

        order_items = []

        for item in user_cart:
            # Process discount information
            offer_id = None
            discounted_price = None
            discounted_shipping = None

            if discount := item.get("discount"):
                offer_id = discount.get("offer_id")
                discounted_price = discount.get("discounted_price")
                discounted_shipping = discount.get("discounted_shipping")

            # Create OrderItem instance (without saving since we are using bulk_create)
            order_items.append(
                cls(
                    order=order,
                    product=products[item["product"]],
                    quantity=item["quantity"],
                    unit_price=item["price"],
                    discounted_price=discounted_price,
                    discounted_shipping=discounted_shipping,
                    offer_id=offer_id,
                    shipping_fee=item["shipping"],
                    selected_attrs=item.get("selected_attrs"),
                )
            )

        return cls.objects.bulk_create(order_items)
