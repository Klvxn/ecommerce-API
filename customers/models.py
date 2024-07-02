import logging
from autoslug import AutoSlugField
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.crypto import get_random_string

from .managers import MyUserManager


logger = logging.getLogger(__name__)


# Create your models here.
class Address(models.Model):
    """
    Represents a customer's shipping or billing address.
    """
    street_address = models.CharField(max_length=30)
    postal_code = models.PositiveIntegerField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=30)

    class Meta:
        verbose_name_plural = "addresses"

    def __str__(self):
        return f"{self.city}, {self.state}"


class Customer(AbstractUser):
    """
    Represents a user of the system who is a customer.

    This model inherits from Django's AbstractUser model and adds additional customer-specific fields

    This model overrides the default username field and required fields 
    to use email as the primary user identifier
    """

    email = models.EmailField(
        "email address", max_length=254, unique=True, db_index=True
    )
    slug = AutoSlugField(always_update=True, populate_from="get_full_name", unique=True)
    date_of_birth = models.DateField(null=True)
    address = models.OneToOneField(Address, on_delete=models.SET_NULL, null=True, blank=True)
    is_vendor = models.BooleanField(default=False)

    products_bought_count = models.PositiveIntegerField(null=True, default=0, blank=True)
    products_bought = models.ManyToManyField("catalogue.Product", blank=True)
    redeemed_vouchers = models.ManyToManyField(
        "catalogue.Voucher", through="catalogue.RedeemedVoucher", blank=True
    )
    username = None

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = MyUserManager()

    def __str__(self):
        return self.email

    def is_first_time_buyer(self, product):
        return product not in self.products_bought.all()


def get_sentinel_user():
    """
    Creates and returns a sentinel user object to be used as a placeholder
    when the original user is deleted.
    
    Returns:
        A User object representing the sentinel user.

    Raises:
        ObjectDoesNotExist: If there's an error creating the user object.
    """
    user_detail = {
        "first_name": "deleted", "last_name": "user", "email": "deleted@none.com"
    }
    while Customer.objects.filter(**user_detail).exists():
        string = get_random_string(5)
        user_detail["email"] = f"deleted{string}@user.com" 
    dummy_password = get_random_string(8)
    user = Customer.objects.create_user(
        **user_detail, is_active=False, password=dummy_password
    )
    logger.warning(f"Creating sentinel user: {user}")
    return user
