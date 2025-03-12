from datetime import datetime, timezone
from decimal import Decimal as D

from django.core.exceptions import ValidationError
from django.db import models

from catalogue.abstract import TimeBased, Timestamp


class Offer(TimeBased):
    """
    Represents discount offers applicable to products or orders based on specific conditions.
    
    Offers can be linked to stores and may require voucher codes for redemption. 
    They serve as containers for various promotional campaigns such as seasonal discounts, 
    flash sales, and special promotions.
    """

    DISCOUNT_TYPE_CHOICES = [
        # ("Free shipping", "Free shipping"),
        ("percentage", "Percentage discount"),
        ("fixed", "Fixed-Amount discount"),
    ]

    OFFER_TYPE_CHOICES = [("product", "Product-level offer"), ("order", "Order-level offer")]
    # Product-level offers apply to specific products or categories and
    # are automatically applied for eligible products and customers.
    # Order-level offers apply to the entire order and are applied at checkout.

    title = models.CharField(max_length=50)
    store = models.ForeignKey("stores.Store", on_delete=models.SET_NULL, null=True, blank=True)
    offer_type = models.CharField(max_length=50, choices=OFFER_TYPE_CHOICES)
    discount_type = models.CharField(max_length=50, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    requires_voucher = models.BooleanField(default=False)
    total_discount_offered = models.DecimalField(
        max_digits=10, decimal_places=2, default=D(0.00), blank=True
    )
    max_discount_allowed = models.DecimalField(max_digits=10, decimal_places=2)

    claimed_by = models.ManyToManyField("customers.Customer", blank=True)

    class Meta(TimeBased.Meta):
        indexes = [
            models.Index(fields=["valid_from", "valid_to"]),
        ]

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        return not (self.valid_from <= datetime.now(timezone.utc) <= self.valid_to)

    # Offer discount type
    @property
    def is_free_shipping(self):
        return False
        # return self.discount_type == self.FREE_SHIPPING

    @property
    def is_percentage_discount(self):
        return self.discount_type == "percentage"

    @property
    def is_fixed_discount(self):
        return self.discount_type == "fixed"
    
    @property
    def maxed_out(self):
        return self.total_discount_offered >= self.max_discount_allowed
    
    @property
    def remaining_discount(self):
        return self.max_discount_allowed - self.total_discount_offered

    # Offer level
    @property
    def for_product(self):
        return self.offer_type == "product"

    @property
    def for_order(self):
        return self.offer_type == "order"

    def claim_offer(self, customer):
        if customer not in self.claimed_by.all():
            self.claimed_by.add(customer)
            
    def apply_discount(self, price):
        """
        Applies the discount to the given price, respecting the maximum discount allowed.        
        Note: This method updates the total_discount_offered field on the offer so should only
        be called when the discount is actually applied.
        
        Args:
            price: The original price to discount
    
        Returns the final price after discount.
        """
        if self.is_free_shipping:
            return D("0.00")

        actual_discount = self.get_discount_amount(price)
    
        # Only update the counter if we're actually applying a discount
        # if actual_discount > 0:
        #     self.update_total_discount(actual_discount)
            
        return price - actual_discount

    def get_discount_amount(self, price, cap=True):
        """
        Calculate the per unit discount that can be applied to a price,
        respecting the maximum discount allowed limit.
        
        Args:
            price: The price to calculate discount for
            cap: Whether to cap the discount at the remaining allowance
            
        Returns:
            Decimal: The actual discount amount that can be applied
        """
        # Calculate the raw discount amount based on discount type
        if self.is_percentage_discount:
            discount = price * D(self.discount_value / 100)
        elif self.is_fixed_discount:
            discount = min(self.discount_value, price)
        else:
            return D("0.0")

        # If no allowance remains, no discount can be given
        if self.remaining_discount < 0:
            return D("0.0")
            
        # Cap the discount at the remaining allowance
        return min(discount, self.remaining_discount) if cap else discount
    
    def update_total_discount(self, amount):
        self.total_discount_offered = models.F("total_discount_offered") + D(amount)
        # validaton check to make sure total_discount_offered is not more than max limit
        self.save(update_fields=["total_discount_offered"])
        self.refresh_from_db(fields=["total_discount_offered"])
        
    def refund_discount(self, amount):
        """
        Returns a discount amount back to the offer's available allowance.
        Called when a discounted item is removed from a cart.
        
        Args:
            amount: The discount amount to refund (positive value)
        """       
        self.total_discount_offered = models.F("total_discount_offered") - D(amount)
        self.save(update_fields=["total_discount_offered"])
        self.refresh_from_db(fields=["total_discount_offered"])

    def satisfies_conditions(self, customer=None, product=None, order=None, voucher=None):
        """
        Checks if all offer conditions are met for application.
        
        Validates offer eligibility based on:
        - Offer time period and active status
        - Customer eligibility criteria
        - Product/category restrictions for product offers
        - Order value requirements for order offers
        - Voucher validity when required
        
        Args:
            customer: Customer applying the offer
            product: Product for product-level offers
            order: Order for order-level offers
            voucher: Voucher code when required
            
        Returns:
            tuple: (is_valid, message) - Boolean validity status and reason
        """
        if customer is None:
            return False, "Customer information is required"

        # Check if the offer is currently active and within its valid time period
        if not self.is_active or self.is_expired:
            return False, "Offer is not currently active/expired"

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

            valid, msg = voucher.is_valid(customer, order.subtotal())
            if not valid:
                return False, msg

        conditions = self.conditions.all()

        # If no conditions and we passed the basic checks, offer is valid
        if not conditions.exists():
            return True, "All conditions satisfied"

        context = {"customer": customer, "product": product, "order": order}

        for condition in conditions:
            return self._check_condition(condition, context)
            # return valid, msg

        return True, "All conditions satisfied"

    def _check_condition(self, condition, context):
        customer = context["customer"]
        if condition.condition_type == "customer_groups":  # Check customer group conditions
            return self.valid_for_customer(customer, condition)

        elif condition.condition_type in ["specific_products", "specific_categories"]:  # Check product-level conditions
            product = context["product"]
            if not self.for_product:
                # This is NOT redundant. It validates that product-specific and categories-specific
                # conditions are only used with product-level offers
                return False, "Invalid Offer"
            return self.valid_for_product(product, customer, condition)

        elif condition.condition_type == "min_order_value":  # Check order-level conditions
            order = context["order"]
            if not self.for_order:
                # It validates that min_order_value conditions are only used
                # with order-level offers
                return False, "Invalid Offer"
            return self.valid_for_order(order, condition)

        return False, "Invalid Offer"

    def valid_for_customer(self, customer, condition=None):
        """
        Validates if the offer is applicable to a specific customer based on customer group conditions.
        
        Args:
            customer: The customer to check eligibility for
            condition: Optional specific condition to check against
            
        Returns:
            If condition is provided: tuple (bool, str) - validity status and reason
            Otherwise: bool indicating if the customer meets conditions
        """
        if condition:
            if condition.eligible_customers == "first_time_buyers":
                if not customer.is_authenticated:
                    return False, "Offer is only valid for registered users"

                elif not customer.is_first_time_buyer:
                    return False, "Offer is only valid for first-time buyers"
            return True, "Valid"
        else:
            customer_conditions = self.conditions.filter(condition_type="customer_groups").first()

            # If no customer group condition exists, the offer is valid for all customers
            if not customer_conditions:
                return True

            eligible_customers = customer_conditions.eligible_customers
            if eligible_customers == "all_customers":
                return True

            elif eligible_customers == "first_time_buyers":
                if customer.is_authenticated and customer.is_first_time_buyer:
                    return True

            return False

    def valid_for_product(self, product, customer, condition=None):
        """
        Checks if the offer is valid for the given product based on product and category eligibility.
        
        Args:
            product: The product to validate against offer conditions
            customer: The customer making the purchase
            condition: Optional specific condition to check against
            
        Returns:
            If condition is provided: tuple (bool, str) - validity status and reason
            Otherwise: bool indicating if the product meets conditions
        """
        # First check if the offer is valid for the customer
        if not self.valid_for_customer(customer):
            return False

        if condition:         
            if condition.condition_type == "specific_products":
                if not condition.eligible_products.filter(id=product.id).exists():
                    return False, "Product is not eligible for this offer"

            elif condition.condition_type == "specific_categories":
                if not condition.eligible_categories.filter(
                    id=product.category.id
                ).exists():
                    return False, "Product category is not eligible for this offer"
            return True, "Valid"
        else:
            product_condition = self.conditions.filter(condition_type="specific_products").first()
            category_condition = self.conditions.filter(condition_type="specific_categories").first()

            # If no product or category conditions exist, the offer is valid for all products
            if not product_condition and not category_condition:
                return True

            # Check product eligibility if a product condition exists
            product_eligible = False
            if product_condition:
                product_eligible = product in product_condition.eligible_products.all()

            # Check category eligibility if a category condition exists
            category_eligible = False
            if category_condition:
                category_eligible = product.category in category_condition.eligible_categories.all()

            return product_eligible or category_eligible

    def valid_for_order(self, order, condition=None):
        """
        Checks if the offer is valid for the given order based on minimum order value.
        
        Args:
            order: The order to validate against the offer conditions
            condition: Optional specific condition to check against
            
        Returns:
            If condition is provided: tuple (bool, str) - validity status and reason
            Otherwise: bool indicating if the order meets all conditions
        """
        if not self.valid_for_customer(order.customer):
            return False

        if condition:
            if order.subtotal() < condition.min_order_value:
                return (
                    False,
                    f"Order value must be more than minimum spend: {condition.min_order_value}",
                )
            return True, "Valid"
        else:
            mov_condition = self.conditions.filter(condition_type="min_order_value").first()

            # If no minimum order value condition exists, offer is valid for all order values
            if not mov_condition:
                return True
            return order.subtotal() >= mov_condition.min_order_value


class OfferCondition(Timestamp):
    """
    Defines eligibility criteria for an offer that determine when it can be applied.
    
    Each offer can have multiple conditions related to:
    - Product eligibility (specific products or categories)
    - Customer segments (like first-time buyers)
    - Order requirements (minimum order value)
    
    The offer is only applied when all associated conditions are satisfied.
    """
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
        help_text="Specify the minimum spend required for the offer to be applicable",
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

    def save(self, *args, **kwargs):
        if self.offer.for_product and self.condition_type not in ["specific_products", "specific_categories"]:
            raise ValueError(f"Condition type {self.condition_type} is not valid for product-level offers.")
        elif self.offer.for_order and self.condition_type != "min_order_value":
            raise ValueError(f"Condition type {self.condition_type} is not valid for order-level offers.")
        super().save(*args, **kwargs)

    def clean(self):
            """
            Validate that only the appropriate fields are set for a given condition_type,
            and that required fields for each type are populated.
            """
            super().clean()
            errors = {}
        
            # Required fields mapping based on condition_type
            required_fields = {
                "specific_products": ["eligible_products"],
                "specific_categories": ["eligible_categories"],
                "customer_groups": ["eligible_customers"],
                "min_order_value": ["min_order_value"],
            }
        
            # Check that required fields are filled for current condition_type
            for field in required_fields.get(self.condition_type, []):
                # if field == "eligible_products":
                #     # For M2M fields, check differently depending on whether instance exists
                #     if self.pk:
                #         if not self.eligible_products.exists():
                #             errors[field] = f"You must select at least one product for '{self.condition_type}'"
                #     elif not hasattr(self, '_eligible_products_cache') or not self._eligible_products_cache:
                #         errors[field] = f"You must select at least one product for '{self.condition_type}'"
                        
                # elif field == "eligible_categories":
                #     # For M2M fields, check differently depending on whether instance exists
                #     if self.pk:
                #         if not self.eligible_categories.exists():
                #             errors[field] = f"You must select at least one category for '{self.condition_type}'"
                #     elif not hasattr(self, '_eligible_categories_cache') or not self._eligible_categories_cache:
                #         errors[field] = f"You must select at least one category for '{self.condition_type}'"
                        
                if field == "eligible_customers" and not self.eligible_customers:
                    errors[field] = f"You must select a customer group for '{self.condition_type}'"
                    
                elif field == "min_order_value" and self.min_order_value is None:
                    errors[field] = f"You must specify a minimum order value for '{self.condition_type}'"
        
            # For reverse checks on M2M fields, only check if instance exists
            if self.pk:
                if self.condition_type != "specific_products" and self.eligible_products.exists():
                    errors["eligible_products"] = f"Products should only be used with 'specific_products' condition type"
                if self.condition_type != "specific_categories" and self.eligible_categories.exists():
                    errors["eligible_categories"] = f"Categories should only be used with 'specific_categories' condition type"
        
            # Regular fields can always be checked
            if self.condition_type != "customer_groups" and self.eligible_customers:
                errors["eligible_customers"] = f"Customer group should only be set for 'customer_groups' condition type"
            if self.condition_type != "min_order_value" and self.min_order_value is not None:
                errors["min_order_value"] = f"Minimum order value should only be set for 'min_order_value' condition type"
        
            if errors:
                raise ValidationError(errors)
    def above_minimum_purchase(self, order_value=0):
        if self.min_order_value and order_value:
            return order_value >= self.min_order_value
        return True


class Voucher(TimeBased):
    """
    Represents a discount code that customers can apply during checkout.
    
    Vouchers are linked to specific offers and control how many times they can be used.
    They support different usage patterns (single-use, multiple-use, once per customer)
    and track redemption history through the RedeemedVoucher model.
    """

    VOUCHER_USAGE = [
        ("single",   "Single use"),
        ("multiple", "Multiple use"),
        ("once_per_customer", "Once for every customer"),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField()
    code = models.CharField(max_length=50, unique=True, db_index=True)
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)
    usage_type = models.CharField(
        max_length=50, choices=VOUCHER_USAGE, default="single"
    )
    max_usage_limit = models.PositiveIntegerField()
    num_of_usage = models.PositiveIntegerField(default=0, blank=True)

    class Meta(TimeBased.Meta):
        indexes = [
            models.Index(fields=["code" ]),
            models.Index(fields=["valid_to", "valid_from"]),
            models.Index(fields=["offer"]),
        ]

    def __str__(self):
        return self.name

    @property
    def single_use(self):
        return self.usage_type == "single"

    @property
    def multiple_use(self):
        return self.usage_type == "multiple"

    @property
    def per_customer(self):
        return self.usage_type == "once_per_customer"

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating:
            self.offer.requires_voucher = True
            self.offer.save(update_fields=["requires_voucher"])

    def update_usage_count(self):
        self.num_of_usage = models.F("num_of_usage") + 1
        self.save(update_fields=["num_of_usage"])

    def within_usage_limits(self, customer=None):
        if self.num_of_usage >= self.max_usage_limit:
            return False
        if self.single_use and self.num_of_usage > 0:
            return False
        if self.per_customer:
            if customer is None or not hasattr(customer, "is_authenticated"):
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
        return True, "Voucher is valid"

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
