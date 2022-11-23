import autoslug
from django.db import models

from customers.models import Customer


# Create your models here.
class Vendor(models.Model):

    customer = models.OneToOneField(Customer, on_delete=models.CASCADE)
    brand_name = models.CharField(max_length=50, unique=True, db_index=True)
    about = models.TextField()
    slug = autoslug.AutoSlugField(populate_from="brand_name", unique=True, always_update=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.brand_name

    def products_count(self):
        return self.product_set.all().count()

    def get_total_products_sold(self):
        return sum(product.sold for product in self.product_set.all())
