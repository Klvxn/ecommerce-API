from decimal import Decimal as D
from datetime import datetime, timezone

from django.core.exceptions import ValidationError
from django.contrib.auth.models import AnonymousUser
from django.db import models

from ..models import BaseModel


class Offer(BaseModel):
    """
    Represents a discount offer model. Offers can be applied to products or shipping fees,
    and can be available to all users, first time buyers or those with voucher code.
    """
    FREE_SHIPPING, PERCENTAGE_DISCOUNT, FIXED_DISCOUNT = (
        "Free shipping", "Percentage discount", "Fixed discount"
    )

    DISCOUNT_TYPE_CHOICES = (
        (FREE_SHIPPING, "Free shipping"),
        (PERCENTAGE_DISCOUNT, "A certain percentage off of a product's price/shipping fee"),
        (FIXED_DISCOUNT, "A fixed amount off of a product's price/shipping fee"),
    )

    ALL_CUSTOMERS, FIRST_TIME_BUYERS, VOUCHERS = ("All customers", "First time buyers", "Vouchers")

    AVAILABLE_TO_CHOICES = (
        (ALL_CUSTOMERS, "The offer is available to all customers"),
        (FIRST_TIME_BUYERS, "First time buyers only can redeem this offer"),
        (VOUCHERS, "Accessible after a customer enters the vouchers code"),
    )

    TARGET = (
        # If the offer is being applied to a product's price or the shipping fee
        ("Product", "product"),
        ("Shipping", "shipping")
    )

    title = models.CharField(max_length=50)
    store = models.ForeignKey("stores.Store", on_delete=models.CASCADE, default=2)
    available_to = models.CharField(max_length=50, null=True, choices=AVAILABLE_TO_CHOICES)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    target = models.CharField(max_length=50, choices=TARGET)
    discount_type = models.CharField(max_length=50, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    total_discount_offered = models.DecimalField(
        max_digits=10, decimal_places=2, default=D(0.0), blank=True
    )
    min_order_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    eligible_products = models.ManyToManyField("catalogue.Product", blank=True)
    claimed = models.ManyToManyField("customers.Customer", blank=True)

    class Meta:
        app_label = "catalogue"

    def __str__(self):
        return self.title

    def clean(self):
        if self.for_product and self.is_free_shipping:
            raise ValidationError({
                "target": "Free shipping can only be applied as a shipping discount"
            })
        super().clean()

    @property
    def has_expired(self):
        return not (self.valid_from <= datetime.now(timezone.utc) <= self.valid_to)

    def above_min_purchase(self, order_value=0):
        if order_value and self.min_order_value is not None:
            return order_value >= self.min_order_value
        return True

    def apply_discount(self, price):
        if self.has_expired:
            return price
        if self.is_free_shipping:
            return D(0.00)
        if self.is_percentage_discount:
            return self.calculate_percent_discount(price)
        if self.is_fixed_discount:
            return self.calculate_fixed_discount(price)

    def calculate_percent_discount(self, price):
        amount_off = price * D(self.discount_value / 100)
        discounted_price = price - round(amount_off, 2)
        return discounted_price

    def calculate_fixed_discount(self, price):
        return price - self.discount_value

    def update_total_discount(self, new_amount):
        self.total_discount_offered += new_amount
        self.save()

    @property
    def is_free_shipping(self):
        return self.discount_type == self.FREE_SHIPPING

    @property
    def is_percentage_discount(self):
        return self.discount_type == self.PERCENTAGE_DISCOUNT

    @property
    def is_fixed_discount(self):
        return self.discount_type == self.FIXED_DISCOUNT

    @property
    def for_product(self):
        return self.target == "Product"

    @property
    def for_shipping(self):
        return self.target == "Shipping"

    @property
    def to_first_time_buyers(self):
        return self.available_to == self.FIRST_TIME_BUYERS

    @property
    def to_all_customers(self):
        return self.available_to == self.ALL_CUSTOMERS

    @property
    def through_vouchers(self):
        return self.available_to == self.VOUCHERS


class Voucher(BaseModel):
    """
    Represents a voucher in the system. Vouchers are tied to offers and can have different
    usage types
    """
    SINGLE, MULTIPLE, ONCE_PER_CUSTOMER = "single", "multiple", "once per customer"

    VOUCHER_USAGE = (
        (SINGLE, "Can only be used once"),
        (MULTIPLE, "Can be used multiple number of times"),
        (ONCE_PER_CUSTOMER, "Can be used once for every customer"),
    )

    name = models.CharField(max_length=50)
    description = models.TextField()
    code = models.CharField(max_length=50, unique=True, db_index=True)
    offer = models.ForeignKey(
        Offer, on_delete=models.CASCADE, limit_choices_to={"available_to": "Vouchers"}
    )
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_type = models.CharField(max_length=50, choices=VOUCHER_USAGE, default=ONCE_PER_CUSTOMER)
    max_usage_limit = models.PositiveIntegerField()
    num_of_usage = models.PositiveIntegerField(default=0, blank=True)

    class Meta:
        app_label = "catalogue"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        super().save(*args, **kwargs)

    def update_usage_count(self):
        self.num_of_usage += 1
        self.save()

    def within_usage_limits(self, customer=None):
        if self.num_of_usage >= self.max_usage_limit:
            return False
        if self.usage_type == self.SINGLE and self.num_of_usage > 0:
            return False
        if self.usage_type == self.ONCE_PER_CUSTOMER:
            if customer is None or isinstance(customer, AnonymousUser):
                return False
            if customer.redeemed_vouchers.filter(id=self.id).exists():
                return False
        return True

    def within_validity_period(self):
        return (
            not self.offer.has_expired and
            self.valid_from < datetime.now(timezone.utc) <= self.valid_to
        )

    def is_valid(self, customer=None, order_value=None):
        if not self.within_usage_limits(customer):
            return False, "Voucher has reached its usage limit"
        if not self.within_validity_period():
            return False, "Voucher offer has expired"
        if not self.offer.above_min_purchase(order_value):
            return False, "Your order is below the required minimum purchase"
        return (
                self.within_usage_limits(customer) and
                self.offer.above_min_purchase(order_value) and
                self.within_validity_period()
        ), "Voucher is valid"

    def redeem(self, customer, order_value):
        valid, _ = self.is_valid(customer, order_value)
        if not valid:
            raise ValidationError(_)
        self.update_usage_count()
        customer.redeemed_vouchers.add(
            self, through_defaults={"date_redeemed": datetime.now(timezone.utc)}
        )
        self.save()

class RedeemedVoucher(models.Model):

    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE)
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE)
    date_redeemed = models.DateTimeField(auto_now_add=True)
    # discount_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.voucher} redeemed by {self.customer}"


