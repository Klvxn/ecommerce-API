from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify


# Create your models here.
User = get_user_model()


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


class Product(models.Model):

    name = models.CharField(max_length=50, unique=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    description = models.TextField()
    image_url = models.URLField()
    stock = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    available = models.BooleanField(default=False)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.stock > 0:
            self.available = True
        return super().save(*args, **kwargs)


class Review(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    review = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
