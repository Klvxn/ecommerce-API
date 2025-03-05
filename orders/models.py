from decimal import Decimal as D
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import models, transaction

from catalogue.abstract import Timestamp
from catalogue.models import Product, ProductVariant
from customers.models import Address

# Create your models here.
User = get_user_model()


class Order(Timestamp):
    class OrderStatus(models.TextChoices):
        PAID = "paid"
        AWAITING_PAYMENT = "awaiting_payment"
        DELIVERED = "delivered"

    id = models.UUIDField(primary_key=True, default=uuid4)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    # billing_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    status = models.CharField(
        choices=OrderStatus.choices,
        default=OrderStatus.AWAITING_PAYMENT,
        max_length=16,
    )
    offer = models.ForeignKey(
        "discount.Offer",
        on_delete=models.SET_NULL,
        related_name="order_offer",
        null=True,
        blank=True,
    )

    # voucher applied to a cart is transferred to the main customer's order and only one voucher per order/cart
    # voucher discounts are calculated and applied to the total
    voucher = models.OneToOneField(
        "discount.Voucher",
        on_delete=models.SET_NULL,
        related_name="order_voucher",
        null=True,
        blank=True,
    )

    # discount amount from the applied voucher 
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=D("0.0"))

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)

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
    def is_paid(self):
        return self.status == self.OrderStatus.PAID

    @property
    def items_count(self):
        return self.items.aggregate(total_items=models.Sum("quantity"))["total_items"] or 0

    def save(self, *args, **kwargs):
        self.total_amount = self.subtotal() + self.total_shipping()
        super().save(*args, **kwargs)

    @property
    def savings_on_items(self):
        return sum([item.savings for item in self.items.all()])

    @property
    def overall_savings(self):
        """
        Total discount offered from applied voucher and active offers on order items
        """
        return (self.savings_on_items + self.discount_amount), (
            self.savings_on_items + self.discount_amount
        ) == (self.original_subtotal - self.subtotal) 

    @property
    def discount_balanced(self):
        return (self.overall_savings) == (self.original_subtotal - self.subtotal) 

    @property
    def subtotal(self):
        # returns the overall order value (including applied discounts on order items)
        total_cost = self.items.aggregate(
            total=models.Sum(
                models.F("total_price"),
                output_field=models.DecimalField(),
            ),
        )
        return total_cost["total"] or 0

    @property
    def original_subtotal(self):
        # returns the overall order value (excluding discounts on order items)
        return (
            self.items.aggregate(
                total=models.Sum(
                    (models.F("unit_price") + models.F("discount_amount")) * models.F("quantity"),
                    output_field=models.DecimalField(),
                ),
            )["total"]
            or 0
        )

    @property
    def total_shipping(self):
        return (
            self.items.aggregate(
                total_shipping=models.Sum(
                    models.F("shipping"),
                    output_field=models.DecimalField(),
                )
            )["total_shipping"]
            or 0
        )


class OrderItem(Timestamp):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=D("0.0"))

    # this is the offer active on the product for the customer before being added to their cart
    offer = models.ForeignKey("discount.Offer", on_delete=models.SET_NULL, null=True, blank=True)
    shipping = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    total_price = models.GeneratedField(
        expression=models.F("unit_price") * models.F("quantity"),
        output_field=models.DecimalField(max_digits=10, decimal_places=2),
        db_persist=True,
    )

    def __str__(self):
        return f"Item {self.id} in Order {self.order}"

    @property
    def savings(self):
        return self.discount_amount * self.quantity if self.discount_amount else 0

    def get_shipping(self):
        return self.shipping

    @classmethod
    def create_from_cart(cls, order, cart):
        """
        Creates OrderItems from the items in the user's cart.

        Args:
            order (Order): The order to which the items should be added.
            cart (Cart): The customer's cart containing items to be added to the order.

        Returns:
            int: The number of records that was created
        """
        order_items = []
        with transaction.atomic():
            try:
                if cart.applied_voucher:
                    order.voucher = cart.applied_voucher
                    order.discount_amount = cart.get_total_voucher_discount()
                    order.save(update_fields=["voucher", "discount_amount"])

            except AttributeError:
                pass
            finally:
                for item_data in cart:
                    offer = item_data.get("active_offer", {})
                    order_items.append(
                        cls(
                            order=order,
                            variant=ProductVariant.objects.get(pk=item_data["variant_id"]),
                            product=Product.objects.get(variants__id=item_data["variant_id"]),
                            unit_price=item_data["price"],
                            discount_amount=item_data["original_price"] - item_data["price"],
                            quantity=item_data["quantity"],
                            shipping=item_data["shipping"],
                            offer_id=offer["offer_id"] if offer["is_valid"] else None,
                        )
                    )
            return cls.objects.bulk_create(order_items)
