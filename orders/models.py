from decimal import Decimal as D
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, transaction

from catalogue.abstract import BaseModel
from catalogue.models import ProductVariant
from discount.models import Offer

# Create your models here.
User = get_user_model()


class Order(BaseModel):
    class OrderStatus(models.TextChoices):
        PAID = "paid"
        AWAITING_PAYMENT = "awaiting_payment"
        DELIVERED = "delivered"
        CANCELLED = "cancelled"

    id = models.UUIDField(primary_key=True, default=uuid4)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    billing_address = models.ForeignKey("customers.Address", on_delete=models.SET_NULL, null=True)
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
            models.Index(fields=["customer", "-created"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return str(self.id)

    @property
    def is_paid(self):
        return self.status == self.OrderStatus.PAID

    @property
    def items_count(self):
        return self.items.aggregate(total_items=models.Sum("quantity"))["total_items"] or 0

    def clean(self):
        if self.offer and not self.offer.valid_for_order(self):
            raise ValidationError("Offer no longer valid for this order")
        return super().clean()

    def save(self, *args, **kwargs):
        self.total_amount = self.subtotal + self.total_shipping - self.discount_amount
        super().save(*args, **kwargs)

    @property
    def savings_on_items(self):
        return sum([item.discount for item in self.items.all()])

    @property
    def overall_savings(self):
        """
        Total discount offered from applied voucher and active offers on order items
        """
        return (self.savings_on_items + self.discount_amount)

    @property
    def discount_balanced(self):
        return (self.original_subtotal - self.subtotal - self.amount_saved) == 0

    @property
    def subtotal(self):
        total_cost = self.items.aggregate(
            total=models.Sum(
                models.F("total_price"),
                output_field=models.DecimalField(),
            ),
        )
        return total_cost["total"] or 0

    @property
    def amount_saved(self):
        """
        Total discount amount from offers on order items.
        """
        return self.discount_amount + (
            self.items.aggregate(
                total=models.Sum(
                    models.F("discount_amount"),
                    output_field=models.DecimalField(),
                ),
            )["total"]
            or 0
        )

    @property
    def original_subtotal(self):
        """
        Total value of items at their original prices (before discounts).
        Calculated as sum (unit_price + discount_amount) * quantity
        """
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


class OrderItem(BaseModel):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    variant = models.ForeignKey("catalogue.ProductVariant", on_delete=models.CASCADE)
    product = models.ForeignKey("catalogue.Product", on_delete=models.CASCADE)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    quantity = models.PositiveIntegerField(default=1)
    shipping = models.DecimalField(max_digits=6, decimal_places=2, null=True)

    # this is the offer and discount active on the product for the customer before being added to their cart
    offer = models.ForeignKey("discount.Offer", on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=D("0.0"))

    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def __str__(self):
        return f"Item {self.id} in Order {self.order}"

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
        variant_ids = [item["variant_id"] for item in cart.cart_items.values()]
        variant_map = ProductVariant.objects.in_bulk(variant_ids)

        if hasattr(cart, "applied_voucher"):
            order.voucher = cart.applied_voucher
            order.discount_amount = cart.get_total_voucher_discount()
            order.save(update_fields=["voucher", "discount_amount"])

        with transaction.atomic():
            for item_data in cart.cart_items.values():
                variant = variant_map[item_data["variant_id"]]
                unit_price, original_price = item_data["price"], item_data["original_price"]
                quantity = item_data["quantity"]
                discount_amount, applied_offer = 0, None

                if applied_offer_id := item_data.get("active_offer", {}).get("offer_id"):
                    applied_offer = Offer.active_objects.filter(id=applied_offer_id).first()

                    if applied_offer and not applied_offer.is_expired:
                        discount_amount = (original_price - unit_price) * quantity
                        applied_offer = applied_offer

                order_items.append(
                    cls(
                        order=order,
                        variant=variant,
                        product=variant.product,
                        unit_price=unit_price,
                        quantity=quantity,
                        total_price=unit_price * quantity,
                        discount_amount=discount_amount,
                        shipping=item_data["shipping"],
                        offer=applied_offer
                    )
                )
            return cls.objects.bulk_create(order_items)
