from autoslug import AutoSlugField
from django.db import models

from customers.models import Customer


# Create your models here.
class Store(models.Model):
    """
    Represents a vendor registered on the system who can list and sell products.

    A Store is linked to a Customer model through a one-to-one relationship. This
    means that a Customer can own a Store, but a single Customer cannot be
    associated with multiple Stores.
    """
    owner = models.OneToOneField(Customer, on_delete=models.CASCADE)
    brand_name = models.CharField(max_length=50, unique=True, db_index=True)
    about = models.TextField()
    followers = models.ManyToManyField(Customer, related_name="following")
    slug = AutoSlugField(populate_from="brand_name", unique=True, always_update=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.brand_name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.customer.is_vendor = True
        self.customer.is_staff = True
        self.customer.save()

    def products_count(self):
        return self.product_set.all().count()

    def get_products_sold(self):
        return sum(product.quantity_sold for product in self.product_set.all())
