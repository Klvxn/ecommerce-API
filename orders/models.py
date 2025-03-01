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
    def total_savings(self):
        return sum([item.savings_on_item_price + item.savings_on_shipping for item in self.items.all()])

    @property
    def items_count(self):
        return self.items.aggregate(total_items=models.Sum("quantity"))["total_items"] or 0

    def save(self, *args, **kwargs):
        self.total_amount = self.subtotal() + self.total_shipping()
        super().save(*args, **kwargs)

    def subtotal(self):
        # returns the overall order value (including applied discounts on order items)
        total_cost = self.items.aggregate(
            total=models.Sum(
                models.F("total_price"),
                output_field=models.DecimalField(),
            ),
        )
        return total_cost["total"] or 0

    def original_subtotal(self):
        # returns the overall order value (excluding discounts on order items)
        return self.items.aggregate(
            total=models.Sum(
                models.F("unit_price") * models.F("quantity"),
                output_field=models.DecimalField(),
            ),
        )["total"] or 0
        
    def total_shipping(self):
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
                voucher = (
                    Voucher.objects.filter(code=voucher_code.upper())
                    .select_related("offer")
                    .get()
                )

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
            for item in items:
                # Check if this product is eligible (if we have restrictions)
                if not offer_to_apply.valid_for_product(item.product):
                    continue
                          
                # Apply the discount to the item's price
                item.discounted_price = offer_to_apply.apply_discount(item.unit_price)
                item.applied_offer = offer_to_apply
                items_to_update.append(item)

        elif offer_to_apply.for_order:
            # For order-level offers, check if the order meets conditions
    
            try:
                # Check minimum order value if specified
                if not offer_to_apply.valid_for_order(self):
                    return None

                # Check customer eligibility if specified
                if not offer_to_apply.valid_for_customer(self.customer):
                    return None

            except AttributeError:
                # If we can't check conditions, proceed anyway
                pass

            # Add the offer to the order itself
            new_subtotal = offer_to_apply.apply_discount(self.original_subtotal())
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
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    quantity = models.PositiveIntegerField(default=1)
    applied_offer = models.ForeignKey(Offer, on_delete=models.SET_NULL, null=True, blank=True)
    shipping = models.DecimalField(max_digits=6, decimal_places=2, null=True)
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

    def savings_on_item_price(self):
        return (
            (self.unit_price - self.discounted_price) * self.quantity
            if self.discounted_price
            else 0
        )

    def savings_on_shipping(self):
        return (self.shipping - self.discounted_shipping) if self.discounted_shipping else 0

    def get_shipping(self):
        return self.discounted_shipping if self.discounted_shipping else self.shipping

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
        for item_data in cart:
            discounted_price = item_data.get("applied_offer", {}).get("discounted_price")
            discounted_shipping = item_data.get("applied_offer", {}).get("discounted_shipping")
            offer_id = item_data.get("applied_offer", {}).get("offer_id")

            # Create OrderItem instance
            order_items.append(
                cls(
                    order=order,
                    variant=ProductVariant.objects.get(pk=item_data["variant_id"]),
                    product=Product.objects.get(variants__id=item_data["variant_id"]),
                    unit_price=item_data["price"],
                    discounted_price=discounted_price,
                    quantity=item_data["quantity"],
                    shipping=item_data["shipping"],
                    discounted_shipping=discounted_shipping,
                    applied_offer_id=offer_id,
                )
            )

        return cls.objects.bulk_create(order_items)
