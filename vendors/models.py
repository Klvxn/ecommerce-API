import autoslug
from django.db import models

from customers.models import Customer


# Create your models here.
class Vendor(models.Model):

    customer = models.OneToOneField(Customer, on_delete=models.CASCADE)
    brand_name = models.CharField(max_length=50, unique=True, db_index=True)
    about = models.TextField()
    slug = autoslug.AutoSlugField(populate_from="brand_name", unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.brand_name

    def products_count(self):
        return self.product_set.all().count()

