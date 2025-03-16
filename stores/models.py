from autoslug import AutoSlugField
from django.db import models



# Create your models here.
class Store(models.Model):
    """
    Represents a store registered on the system that can list and sell products.

    A Store is linked to a Customer model through a one-to-one relationship. This
    means that a Customer can own a Store, but a single Customer cannot be
    associated with multiple Stores.
    """

    owner = models.OneToOneField("customers.Customer", on_delete=models.CASCADE)
    name = models.CharField(max_length=50, unique=True, db_index=True)
    about = models.TextField()
    followers = models.ManyToManyField("customers.Customer", related_name="following", blank=True)
    slug = AutoSlugField(populate_from="name", unique=True, always_update=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    address = models.OneToOneField("customers.Address", on_delete=models.RESTRICT, null=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    @property
    def followers_count(self):
        return self.followers.count()

    @property
    def products_count(self):
        return self.product_set.count()

    @property
    def products_sold(self):
        return sum(product.quantity_sold for product in self.product_set.all())
