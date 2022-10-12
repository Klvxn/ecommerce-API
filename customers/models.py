from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify

from .managers import MyUserManager


# Create your models here.
class Address(models.Model):

    street_address = models.CharField(max_length=30)
    postal_code = models.PositiveIntegerField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.city}, {self.state}"


class Customer(AbstractUser):

    email = models.EmailField(("Email address"), max_length=254, unique=True)
    slug = models.SlugField()
    date_of_birth = models.DateField(("Date Of Birth"), null=True)
    address = models.OneToOneField(Address, on_delete=models.SET_NULL, null=True)

    username = None

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = MyUserManager()

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.first_name} {self.last_name}")
        return super().save(*args, **kwargs)
