import logging
from datetime import datetime, timezone

from autoslug import AutoSlugField
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.crypto import get_random_string

from .managers import MyUserManager

logger = logging.getLogger(__name__)


# Create your models here.
class Customer(AbstractUser):
    """
    Represents a user of the system who is a customer.

    This model inherits from Django's AbstractUser model and adds additional customer-specific fields

    This model overrides the default username field and required fields
    to use email as the primary user identifier
    """
    email = models.EmailField("email address", max_length=254, unique=True, db_index=True)
    slug = AutoSlugField(always_update=True, populate_from="get_full_name", unique=True)
    date_of_birth = models.DateField(null=True)
    is_vendor = models.BooleanField(default=False)

    last_purchase_date = models.DateTimeField(null=True, blank=True)
    products_bought_count = models.PositiveIntegerField(
        null=True, default=0, blank=True, help_text="Number of unique products purchased"
    )
    total_units_bought = models.PositiveIntegerField(
        null=True,
        default=0,
        blank=True,
        help_text="Sum of all quantities purchased across all products",
    )
    products_bought = models.ManyToManyField(
        "catalogue.ProductVariant",
        through="customers.PurchaseRecord",
        through_fields=("customer", "product_variant"),
        blank=True,
    )
    redeemed_vouchers = models.ManyToManyField(
        "discount.Voucher", through="discount.RedeemedVoucher", blank=True
    )
    username = None

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = MyUserManager()

    def __str__(self):
        return self.email

    @property
    def is_first_time_buyer(self):
        return not self.products_bought.exists()

    def update_purchases_count(self):
        self.products_bought_count = self.purchases.count()
        self.total_units_bought = (
            self.purchases.aggregate(total=models.Sum("extra__quantity"))["total"] or 0
        )
        self.last_purchase_date = datetime.now(timezone.utc)
        self.save(
            update_fields=["products_bought_count", "total_units_bought", "last_purchase_date"]
        )

    def frequently_bought_products(self, min_units=3):
        return self.products_bought.annotate(
            total_units=models.Sum("purchases__extra__quantity")
        ).filter(total_units__gt=min_units)


def get_sentinel_user():
    """
    Creates and returns a sentinel user object to be used as a placeholder
    when the original user is deleted.

    Returns:
        A User object representing the sentinel user.

    Raises:
        ObjectDoesNotExist: If there's an error creating the user object.
    """
    user_detail = {"first_name": "deleted", "last_name": "user", "email": "deleted@none.com"}
    while Customer.objects.filter(**user_detail).exists():
        string = get_random_string(5)
        user_detail["email"] = f"deleted{string}@user.com"
    dummy_password = get_random_string(8)
    user = Customer.objects.create_user(**user_detail, is_active=False, password=dummy_password)
    logger.warning(f"Creating sentinel user: {user}")
    return user


class Address(models.Model):
    """
    Represents a customer's shipping or billing address.
    """
    street_address = models.CharField(max_length=30)
    postal_code = models.PositiveIntegerField()
    customer = models.OneToOneField(
        "customers.Customer", on_delete=models.SET_NULL, null=True, blank=True
    )
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=30)

    class Meta:
        verbose_name_plural = "addresses"

    def __str__(self):
        return f"{self.city}, {self.state}, {self.country}"


class PurchaseRecord(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.SET(get_sentinel_user), related_name="purchases"
    )
    product_variant = models.ForeignKey(
        "catalogue.ProductVariant", on_delete=models.SET_NULL, null=True
    )
    order = models.ForeignKey("orders.Order", on_delete=models.SET_NULL, null=True)
    extra = models.JSONField(null=True, default=dict)
    purchased_at = models.DateTimeField(auto_now_add=True)
