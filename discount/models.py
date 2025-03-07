from datetime import datetime, timezone
from decimal import Decimal as D

from django.core.exceptions import ValidationError
from django.contrib.auth.models import AnonymousUser
from django.db import models

from catalogue.abstract import TimeBased, Timestamp


class ActiveOfferManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                valid_from__lte=datetime.now(timezone.utc),
                valid_to__gt=datetime.now(timezone.utc),
                # is_active=True,
            )
        )


class Offer(TimeBased):
    """
    Represents a discount offer model. Offers can be applied to products or shipping fees,
    and can be available to all users, first time buyers or those with voucher code.
    """

    FREE_SHIPPING, PERCENTAGE_DISCOUNT, FIXED_DISCOUNT = (
        "Free shipping",
        "Percentage discount",
        "Fixed discount",
    )

    DISCOUNT_TYPE_CHOICES = (
        (FREE_SHIPPING, "Free shipping"),
        (PERCENTAGE_DISCOUNT, "A certain percentage off of a product's price"),
        (FIXED_DISCOUNT, "A fixed amount off of a product's price"),
    )

    APPLIES_TO_CHOICES = (
        # If the offer is being applied to a product or customer's order
        ("Product", "The offer is applicable to specific products"),  # Product-level offer
        ("Order", "Applicable to the customer's order "),  # Order-level offer
    )

    title = models.CharField(max_length=50)
    store = models.ForeignKey("stores.Store", on_delete=models.SET_NULL, null=True, blank=True)
    applies_to = models.CharField(max_length=50, choices=APPLIES_TO_CHOICES)
    discount_type = models.CharField(max_length=50, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    requires_voucher = models.BooleanField(default=False)
    total_discount_offered = models.DecimalField(
        max_digits=10, decimal_places=2, default=D(0.00), blank=True
    )
    max_discount_allowed = models.DecimalField(max_digits=10, decimal_places=2)

    claimed_by = models.ManyToManyField("customers.Customer", blank=True)

    objects = ActiveOfferManager()

    class Meta:
        indexes = [
            models.Index(fields=["valid_from", "valid_to"]),
            models.Index(fields=["store"]),
        ]

    def __str__(self):
        return self.title

    # def clean(self):
    #     if self.for_product and self.is_free_shipping:
    #         raise ValidationError({"target": "Free shipping can only be applied as a shipping discount"})
    #     if self.for_order and self.is_free_shipping:
    #         raise ValidationError({"target": "Free shipping can only be applied as a shipping discount"})
    #     super().clean()

    @property
    def is_expired(self):
        return not (self.valid_from <= datetime.now(timezone.utc) <= self.valid_to)

    # Offer discount type
    @property
    def is_free_shipping(self):
        return self.discount_type == self.FREE_SHIPPING

    @property
    def is_percentage_discount(self):
        return self.discount_type == self.PERCENTAGE_DISCOUNT

    @property
    def is_fixed_discount(self):
        return self.discount_type == self.FIXED_DISCOUNT

    # Offer Target
    @property
    def for_product(self):
        return self.applies_to == "Product"

    @property
    def for_order(self):
        return self.applies_to == "Order"

    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)
        # if self.for_order and self.conditions.eligible_products is not None:
        #     raise ValidationError("Offers targeted to orders cannot have eligible products")
        # super().save(*args, **kwargs)

    def apply_discount(self, price):
        if self.is_free_shipping:
            return D(0.00)
        elif self.is_percentage_discount:
            return self.calc_percentage_discount(price)
        elif self.is_fixed_discount:
            return self.calc_fixed_discount(price)
        else:
            return price

    def calc_percentage_discount(self, price):
        amount_off = price * D(self.discount_value / 100)
        discounted_price = price - round(amount_off, 2)
        return discounted_price

    def calc_fixed_discount(self, price):
        return price - self.discount_value

    def discount_amount(self, price):
        if self.is_percentage_discount:
            return price * D(self.discount_value / 100)
        elif self.is_fixed_discount:
            return self.discount_value

    def update_total_discount(self, new_amount):
        self.total_discount_offered += D(new_amount)
        self.save()

    def satisfies_conditions(self, customer=None, product=None, order=None, voucher=None):
        """
        Comprehensive method to check if all conditions for an offer are satisfied,
        including voucher validation when required.

        This method serves as a single source of truth for offer validity by checking:
        - Basic offer validity (time period, active status)
        - Customer eligibility
        - Product/category eligibility (for product-level offers)
        - Order conditions like minimum order value (for order-level offers)
        - Store restrictions
        - Voucher validity and usage limits when required

        Args:
            order: Order object, required for order-level offers
            product: Product object, required for product-level offers
            customer: Customer object, required for all checks
            voucher: Voucher object, required if the offer requires a voucher

        Returns:
            tuple: (bool, str) - (whether conditions are satisfied, reason if not satisfied)
        """
        if customer is None:
            return False, "Customer information is required"

        if self.for_product and product is None:
            return False, "Product information is required for product-level offers"

        if self.for_order and order is None:
            return False, "Order information is required for order-level offers"

        # Handle voucher requirement checks
        if self.requires_voucher:
            if voucher is None:
                return False, "This offer requires a valid voucher code"

            # Verify the voucher is associated with this offer
            if voucher.offer_id != self.id:
                return False, "Invalid voucher for this offer"

            if not voucher.within_usage_limits(customer):
                return False, "Voucher has reached its maximum usage limit"

            if not voucher.within_validity_period():
                return False, "Voucher has expired"

            # For order-level offers, check minimum purchase requirement
            if self.for_order:
                order_value = order.subtotal()
                if not voucher.offer.above_min_purchase(order_value):
                    return (
                        False,
                        "Order value is below the minimum purchase requirement for this voucher",
                    )

        # Check if the offer is currently active and within its valid time period
        if not self.is_active:
            return False, "Offer is not currently active"

        if self.is_expired:
            return False, "Offer has expired"

        # Check store restrictions if applicable
        if self.store and (
            (self.for_product and product.store != self.store)
            or (self.for_order and order.store != self.store)
        ):
            return False, "Offer is not valid for this store"

        conditions = self.conditions.all()

        # If there are no conditions and we passed the basic checks, the offer is valid
        if not conditions.exists():
            return True, "All conditions satisfied"

        for condition in conditions:
            # Check customer group conditions
            if condition.condition_type == "customer_groups":
                if condition.eligible_customers == "first_time_buyers":
                    if not customer.is_authenticated:
                        return False, "Offer is only valid for registered users"

                    elif not customer.is_first_time_buyer:
                        return False, "Offer is only valid for first-time buyers"

            # Check product-specific conditions for product-level offers
            elif self.for_product:
                if condition.condition_type == "specific_products":
                    if not condition.eligible_products.filter(id=product.id).exists():
                        return False, "Product is not eligible for this offer"

                elif condition.condition_type == "specific_categories":
                    if not condition.eligible_categories.filter(
                        id=product.category.id
                    ).exists():
                        return False, "Product category is not eligible for this offer"

            # Check order-level conditions
            elif self.for_order:
                if condition.condition_type == "min_order_value":
                    if order.subtotal() < condition.min_order_value:
                        return (
                            False,
                            f"Order value must be at least {condition.min_order_value}",
                        )

        return True, "All conditions satisfied"

    def valid_for_customer(self, customer):
        """
        Checks if the offer is valid for the given customer based on customer group conditions.
        """
        cust_group_cond = self.conditions.filter(condition_type="customer_groups").first()

        # If no customer group condition exists, the offer is valid for all customers
        if not cust_group_cond:
            return True

        eligible_customers = cust_group_cond.eligible_customers

        # If eligible for all customers, or customer is a first-time buyer when that's required
        if eligible_customers == "all_customers":
            return True

        if eligible_customers == "first_time_buyers":
            if customer.is_authenticated and customer.is_first_time_buyer:
                return True

        return False

    def valid_for_product(self, product, customer):
        """
        Checks if the offer is valid for the given product based on product and category conditions.
        """
        # First check if the offer is valid for the customer
        if not self.valid_for_customer(customer):
            return False

        condition_for_product = self.conditions.filter(
            condition_type="specific_products"
        ).first()
        condition_for_category = self.conditions.filter(
            condition_type="specific_categories"
        ).first()

        # If no product or category conditions exist, the offer is valid for all products
        if not condition_for_product and not condition_for_category:
            return True

        # Check product eligibility if a product condition exists
        product_eligible = False
        if condition_for_product:
            product_eligible = product in condition_for_product.eligible_products.all()

        # Check category eligibility if a category condition exists
        category_eligible = False
        if condition_for_category:
            category_eligible = (
                product.category in condition_for_category.eligible_categories.all()
            )

        return product_eligible or category_eligible

    def valid_for_order(self, order):
        """
        Checks if the offer is valid for the given order based on minimum order value conditions.
        """
        # First check if the offer is valid for the customer
        if not self.valid_for_customer(order.customer):
            return False

        mov_condition = self.conditions.filter(condition_type="min_order_value").first()

        # If no minimum order value condition exists, the offer is valid for all order values
        if not mov_condition:
            return True

        return order.subtotal() >= mov_condition.min_order_value


class OfferCondition(Timestamp):
    CONDITIONS = [
        ("specific_products", "Specific Products"),
        ("specific_categories", "Specific Categories"),
        ("customer_groups", "Customer Groups"),
        ("min_order_value", "Minimum Order Value"),
    ]
    CUSTOMER_GROUPS = [
        ("first_time_buyers", "First Time Buyers"),
        ("all_customers", "All Customers"),
    ]

    condition_type = models.CharField(max_length=20, choices=CONDITIONS)
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="conditions")
    min_order_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Specify the minimum order amount required for this offer to be applicable",
    )
    eligible_customers = models.CharField(
        max_length=20, choices=CUSTOMER_GROUPS, null=True, blank=True
    )
    eligible_products = models.ManyToManyField("catalogue.Product", blank=True)
    eligible_categories = models.ManyToManyField("catalogue.Category", blank=True)

    class Meta:
        unique_together = ("condition_type", "offer")

    def __str__(self):
        return f"Conditions for {self.offer}"

    def above_min_purchase(self, order_value=0):
        if order_value and self.min_order_value is not None:
            return order_value >= self.min_order_value
        return True


class Voucher(TimeBased):
    """
    Vouchers are tied to offers with different usage types
    """

    SINGLE, MULTIPLE, ONCE_PER_CUSTOMER = "single", "multiple", "once per customer"

    VOUCHER_USAGE = (
        (SINGLE, "Can only be used once"),
        (MULTIPLE, "Can be used multiple number of times"),
        (ONCE_PER_CUSTOMER, "Can be used once for every customer"),
    )

    name = models.CharField(max_length=255)
    description = models.TextField()
    code = models.CharField(max_length=50, unique=True, db_index=True)
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)
    usage_type = models.CharField(
        max_length=50, choices=VOUCHER_USAGE, default=ONCE_PER_CUSTOMER
    )
    max_usage_limit = models.PositiveIntegerField()
    num_of_usage = models.PositiveIntegerField(default=0, blank=True)

    objects = ActiveOfferManager()

    class Meta:
        indexes = [
            models.Index(fields=["code", "valid_to"]),
            models.Index(fields=["offer", "usage_type"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating:
            self.offer.requires_voucher = True
            self.offer.save(update_fields=["requires_voucher"])

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
            return not RedeemedVoucher.objects.filter(voucher=self, customer=customer).exists()
        return True

    def within_validity_period(self):
        return (
            not self.offer.is_expired
            and self.valid_from < datetime.now(timezone.utc) <= self.valid_to
        )

    def is_valid(self, customer=None, order_value=None):
        if customer and not self.within_usage_limits(customer):
            return False, "Voucher has reached its usage limit"
        if not self.within_validity_period():
            return False, "Voucher offer has expired"
        if order_value and not self.offer.above_min_purchase(order_value):
            return False, "Your order is below the required minimum purchase"
        return (
            self.within_usage_limits(customer)
            and self.offer.above_min_purchase(order_value)
            and self.within_validity_period()
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
