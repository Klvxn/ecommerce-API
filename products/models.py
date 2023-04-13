from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify

from vendors.models import Vendor


# Create your models here.
User = get_user_model()


def get_sentinel_user():
    user_detail = {"first_name": "None", "last_name": "None", "email": "user@none.com"}
    return User.objects.create_user(**user_detail)


class BaseModel(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    # image = models.ImageField(upload_to="%(app_label)s_%(class)/")

    class Meta:
        abstract = True


class Category(models.Model):

    name = models.CharField(max_length=50, db_index=True)
    slug = models.SlugField()

    class Meta:
        ordering = ["name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)


class Product(BaseModel):

    name = models.CharField(max_length=50, unique=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    description = models.TextField()
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True)
    image_url = models.URLField()
    stock = models.PositiveIntegerField()
    sold = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    label = models.CharField(max_length=50, null=True, blank=True)
    available = models.BooleanField(default=False)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.stock > 0:
            self.available = True
        else:
            self.available = False
        return super().save(*args, **kwargs)

    def get_latest_reviews(self):
        return self.reviews.values("id", "user__email", "review", "created").order_by("-created")[:10]


class Review(BaseModel):

    class Ratings(models.IntegerChoices):
        VERY_BAD = 1
        UNSATISFIED = 2
        JUST_THERE = 3
        SATISFIED = 4
        VERY_SATISFIED = 5

    user = models.ForeignKey(User, on_delete=models.SET(get_sentinel_user))
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    review = models.TextField()
    image_url = models.URLField(null=True)
    rating = models.IntegerField(choices=Ratings.choices, default=3)

    class Meta:
        get_latest_by = "created"
