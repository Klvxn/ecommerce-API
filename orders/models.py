from decimal import Decimal as D
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.db.models import Case, F, When

from catalogue.models import Product, ProductVariant, Timestamp
from customers.models import Address
from discount.models import Offer, Voucher


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
    applied_offer = models.ForeignKey(
        Offer,
        on_delete=models.SET_NULL,
        related_name="order_offer",
        null=True,
        blank=True,
    )
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
        """
        Get the total quantity of all items in the order.

        Returns:
            int: Total quantity of items.
        """
        return self.items.aggregate(total_items=models.Sum("quantity"))["total_items"] or 0

    def save(self, *args, **kwargs):
        self.total_amount = self.subtotal() + self.total_shipping()
        super().save(*args, **kwargs)

    def subtotal(self):
        """
        Calculate the subtotal of the order, excluding shipping and discounts.

        Returns:
            Decimal: The total cost of the order.
        """
        total_cost = self.items.aggregate(
            total=models.Sum(
                models.F("total_price"),
                output_field=models.DecimalField(),
            ),
        )
        return total_cost["total"] or 0

    def total_shipping(self):
        """
        Calculates the total shipping fee for the order.

        Returns:
            Decimal: The total shipping fee for all items in the order.
        """
        return (
            self.items.aggregate(
                total_shipping=models.Sum(
                    models.F("discounted_shipping"),
                    output_field=models.DecimalField(),
                )
            )["total_shipping"]
            or 0
        )

    @transaction.atomic
    def apply_offer(self, offer=None, voucher_code=None):
        """
        Apply an offer or voucher to the order items if eligible.

        This method handles both direct offers (typically from promotions) and
        voucher-based offers. It applies the appropriate discounts to eligible
        order items based on the offer's type and target.

        Args:
            offer (Offer, optional): A direct offer to apply. Default is None.
            voucher_code (str, optional): The code of a voucher to redeem. Default is None.

        Returns:
            Offer or None: The applied offer if successfully applied, otherwise None.
        """
        # Validate input: either offer or voucher_code must be provided, but not both
        if not (offer or voucher_code) or (offer and voucher_code):
            return None

        # If voucher code is provided, try to get the associated offer
        if voucher_code:
            try:
                voucher = Voucher.objects.filter(code=voucher_code.upper()).select_related("offer").get()

                if not voucher.is_valid():
                    return None

                offer_to_apply = voucher.offer
                voucher.update_usage_count()

            except Voucher.DoesNotExist:
                return None
        else:
            offer_to_apply = offer

        # Fetch all items in the order with their related products
        items = self.items.select_related("product").all()
        if not items:
            return None

        # Track which items will need updating
        items_to_update = []

        # Handle different offer types
        if offer_to_apply.is_free_shipping:
            # Apply free shipping to all items
            for item in items:
                item.discounted_shipping = D("0.00")
                item.applied_offer = offer_to_apply
                items_to_update.append(item)

        elif offer_to_apply.for_product:
            # For product-level offers, we need to check eligibility per product
            eligible_product_ids = []

            # Get eligible products if there are conditions
            try:
                condition = offer_to_apply.conditions.filter(condition_type="specific_products").first()
                if condition:
                    eligible_product_ids = list(condition.eligible_products.values_list("id", flat=True))
            except AttributeError:
                # If there's no condition, assume all products are eligible
                pass

            for item in items:
                # Check if this product is eligible (if we have restrictions)
                if eligible_product_ids and item.product.id not in eligible_product_ids:
                    continue

                # Apply the discount to the item's price
                item.discounted_price = offer_to_apply.apply_discount(item.unit_price)
                item.applied_offer = offer_to_apply
                items_to_update.append(item)

        elif offer_to_apply.for_order:
            # For order-level offers, check if the order meets conditions
            try:
                conditions = offer_to_apply.conditions.filter(
                    condition_type__in=["min_order_value", "customer_groups"]
                )
                for condition in conditions:
                    # Check minimum order value if specified
                    if condition.min_order_value is not None:
                        if self.subtotal() < condition.min_order_value:
                            return None

                    # Check customer eligibility if specified
                    if condition.eligible_customers == "first_time_buyers" and not getattr(
                        self.customer, "is_first_time_buyer", False
                    ):
                        return None
            except AttributeError:
                # If we can't check conditions, proceed anyway
                pass

            # Add the offer to the order itself
            new_subtotal = offer_to_apply.apply_discount(self.subtotal())
            self.total_amount = new_subtotal + self.total_shipping()
            self.applied_offer = offer_to_apply
            self.save()

        # Only update if we have items to update
        if items_to_update:
            # Bulk update order items with the applied discounts
            OrderItem.objects.bulk_update(
                items_to_update, ["discounted_price", "discounted_shipping", "applied_offer"]
            )

            # Update total amount for the order
            return offer_to_apply

        return None


class OrderItem(Timestamp):
    """
    Represents an individual item within an order.
    """

    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    quantity = models.PositiveIntegerField(default=1)
    applied_offer = models.ForeignKey(Offer, on_delete=models.SET_NULL, null=True, blank=True)
    shipping_fee = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    discounted_shipping = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    total_price = models.GeneratedField(
        expression=Case(
            When(discounted_price__isnull=False, then=F("discounted_price") * F("quantity")),
            default=F("unit_price") * F("quantity"),
        ),
        output_field=models.DecimalField(max_digits=10, decimal_places=2),
        db_persist=True,
    )

    def __str__(self):
        return f"Item {self.id} in Order {self.order}"

    @property
    def savings(self):
        return (self.unit_price - self.discounted_price) * self.quantity if self.discounted_price else 0

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
        order_items = []
        for item_data in user_cart:
            discounted_price = item_data.get("discount", {}).get("discounted_price")
            discounted_shipping = item_data.get("discount", {}).get("discounted_shipping")
            offer_id = item_data.get("discount", {}).get("offer_id")

            # Create OrderItem instance
            order_items.append(
                cls(
                    order=order,
                    variant=ProductVariant.objects.get(pk=item_data["variant_id"]),
                    product=Product.objects.get(pk=item_data["product_id"]),
                    unit_price=item_data["price"],
                    discounted_price=discounted_price,
                    quantity=item_data["quantity"],
                    shipping_fee=item_data["shipping"],
                    discounted_shipping=discounted_shipping,
                    applied_offer_id=offer_id,
                )
            )

        return cls.objects.bulk_create(order_items)
