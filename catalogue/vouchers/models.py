from decimal import Decimal as D
from datetime import datetime, timezone

from django.core.exceptions import ValidationError
from django.contrib.auth.models import AnonymousUser
from django.db import models


class Offer(models.Model):

    FREE_SHIPPING, PERCENTAGE_DISCOUNT, FIXED_DISCOUNT = (
        "Free shipping", "Percentage discount", "Fixed discount"
    )
    DISCOUNT_TYPE = (
        (FREE_SHIPPING, "Free shipping"),
        (PERCENTAGE_DISCOUNT, "A certain percentage off of the customer's order/shipping fee"),
        (FIXED_DISCOUNT, "A fixed amount off of the customer's order/shipping fee"),
    )
    THROUGH_VOUCHERS, FIRST_TIME_BUYERS, ALL_USERS = ("Vouchers", "First time buyers", "All users")
    APPLIED_TO = (
        (THROUGH_VOUCHERS, "Accessible after a customer enters the vouchers code"),
        (ALL_USERS, "The offer is applicable to all customers"),
        (FIRST_TIME_BUYERS, "first time buyers only can redeem this offer"),
    )
    TARGET = (
        ("Product", "product"),
        ("Shipping", "shipping")
    )
    title = models.CharField(max_length=50)
    applied_to = models.CharField(max_length=50, choices=APPLIED_TO)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    # Discount benefits that comes with the offer
    target = models.CharField(max_length=50, choices=TARGET)
    discount_type = models.CharField(max_length=50, choices=DISCOUNT_TYPE)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    total_discount_offered = models.DecimalField(
        max_digits=10, decimal_places=2, default=D(0.0), blank=True
    )
    minimum_order_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    eligible_products = models.ManyToManyField("catalogue.Product", blank=True)

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

    def apply_discount(self, price):
        if self.has_expired:
            return price
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
        return self.applied_to == self.FIRST_TIME_BUYERS

    @property
    def to_all_users(self):
        return self.applied_to == self.ALL_USERS

    @property
    def to_vouchers(self):
        return self.applied_to == self.THROUGH_VOUCHERS


class Voucher(models.Model):
    SINGLE, MULTIPLE, ONCE_PER_CUSTOMER = "single", "multiple", "once per customer"

    VOUCHER_USAGE = (
        (SINGLE, "Can only be used once"),
        (MULTIPLE, "Can be used multiple number of times"),
        (ONCE_PER_CUSTOMER, "Can be used once for every customer"),
    )

    name = models.CharField(max_length=50)
    description = models.TextField()
    code = models.CharField(max_length=50, unique=True)
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_type = models.CharField(max_length=50, choices=VOUCHER_USAGE, default=ONCE_PER_CUSTOMER)
    max_usage = models.PositiveIntegerField()
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

    def check_usage_validity(self, customer=None):
        if self.num_of_usage >= self.max_usage:
            return False
        if self.usage_type == self.SINGLE and self.num_of_usage > 0:
            return False
        if self.usage_type == self.ONCE_PER_CUSTOMER:
            if customer is None or isinstance(customer, AnonymousUser):
                return False
            if customer.redeemed_vouchers.filter(id=self.id).exists():
                return False
        return True

    def above_mov(self, order_value=0):
        if order_value and self.offer.minimum_order_value is not None:
            return order_value >= self.offer.minimum_order_value
        return True

    def within_validity_period(self):
        return self.valid_from < datetime.now(timezone.utc) <= self.valid_to

    def is_valid(self, customer=None, order_value=None):
        if not self.check_usage_validity(customer):
            return False, "Voucher has reached its usage limit"
        if not self.within_validity_period():
            return False, "Voucher offer has expired"
        if not self.above_mov(order_value):
            return False, "Your order is below the required minimum purchase"
        return (
                self.check_usage_validity(customer) and
                self.above_mov(order_value) and
                self.within_validity_period()
        ), "Voucher is Valid"

    def redeem(self, customer, order_value):
        valid, _ = self.is_valid(customer, order_value)
        if not valid:
            raise ValidationError("This vouchers is no longer valid.")
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


