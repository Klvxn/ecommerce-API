from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify

from customers.models import get_sentinel_user
from stores.models import Store
from .vouchers.models import Voucher, Offer


# Create your models here.
User = get_user_model()


class BaseModel(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(models.Model):
    """
    Model representing a category for products.
    """
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
    """
    Model representing a product.
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    description = models.TextField()
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True)
    image_url = models.URLField()
    in_stock = models.PositiveIntegerField()
    quantity_sold = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    available = models.BooleanField(default=False)
    rating = models.FloatField(null=True, blank=True)

    objects = models.Manager()

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.in_stock > 0:
            self.available = True
        else:
            self.available = False
        super().save(*args, **kwargs)
        
    def update_rating(self):
        """
        Updates the rating field of the product with value from the 
        `calculate_rating` method.
        
        Returns:
            None
        """
        self.rating = self.calculate_rating()
        self.save()
    
    def calculate_rating(self):
        """
        Calculate the average rating of the product based on its 
        associated reviews.
        
        Returns:
            float or None: The calculated average rating, or None if no reviews.
        """
        results = self.reviews.aggregate(
            sum=models.Sum("rating"), count=models.Count("id")
        )
        rating_sum, reviews_count = results.values()
        return rating_sum / reviews_count if reviews_count else None

    def get_latest_reviews(self):
        """
        Get the latest reviews for the product.

        Returns:
            QuerySet: The latest 10 reviews for the product.
        """
        return self.reviews.values("id", "user__email", "review", "created").order_by("-created")[:10]


class ProductAttribute(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="attributes"
    )
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}: {self.values.values_list('value', flat=True)}"

    class Meta:
        verbose_name = "product attribute"
        unique_together = ("product", "name")


class ProductAttributeValue(models.Model):
    attribute = models.ForeignKey(
        ProductAttribute, on_delete=models.CASCADE, related_name="values"
    )
    value = models.CharField(max_length=255)

    def __str__(self):
        return f" {self.value}"

    class Meta:
        verbose_name = "attribute value"
        verbose_name_plural = "attribute values"
        unique_together = ("value", "attribute")


class Review(BaseModel):
    """
    Model representing a review for a product.
    """
    class Ratings(models.IntegerChoices):
        VERY_BAD = 1, "Very Bad"
        UNSATISFIED = 2, "Unsatisfied"
        JUST_THERE = 3, "Just There"
        SATISFIED = 4, "Satisfied"
        VERY_SATISFIED = 5, "Very Satisfied"

    # TODO: Sentiment analysis with BERT for reviews
    SENTIMENT_TYPES = (
        ("POSITIVE", "Positive sentiment"),
        ("Neutral", "Neutral sentiment"),
        ("Negative", "Negative sentiment"),
    )

    user = models.ForeignKey(User, on_delete=models.SET(get_sentinel_user))
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    review = models.TextField()
    image_url = models.URLField(null=True, blank=True)
    rating = models.IntegerField(choices=Ratings.choices, default=0)
    sentiment = models.CharField(max_length=50, null=True, choices=SENTIMENT_TYPES)
    sentiment_score = models.FloatField(null=True)

    class Meta:
        get_latest_by = "created"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.product.update_rating()
        
    def __str__(self):
        return f"Review of {self.product.name} by {self.user}"