from datetime import datetime, timezone
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from customers.models import get_sentinel_user
from vendors.models import Vendor
from .managers import DiscountQuerySet


# Create your models here.
User = get_user_model()


class BaseModel(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Discount(BaseModel):
    """
    Model representing a discount which can be applied to orders or products.
    """
    
    DISCOUNT_TYPES = (
        ("order_discount", "Order discount"),
        ("product_discount", "Product discount")
    )
    
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default="product_discount")
    description = models.TextField()
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    active = models.BooleanField(default=False)
    valid_from = models.DateTimeField()
    minimum_order_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_to = models.DateTimeField()
    owner = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    
    objects = DiscountQuerySet.as_manager()

    def __str__(self):
        return self.name
    
    def clean(self):
        """
        Validate the discount model fields.
        
        Raises:
            ValidationError: If the discount type is order_discount and minimum_order_value is not set.
        """
        if self.discount_type == "order_discount" and self.minimum_order_value is None:
            raise ValidationError({
                "minimum_order_value": "Minimum order value is required for order discounts"
            })
        super().clean()
        
    def is_valid(self):
        """
        Check if the discount is currently active and within the valid date range.

        Returns:
            bool: True if the discount is valid, False otherwise.
        """
        return self.active and self.valid_from <= datetime.now(timezone.utc) <= self.valid_to
    
    def apply_discount(self, price):
        """
        Applies the discount to the given price if the discount is valid.

        Args:
            price: The original price before discount.
            discount: The Discount object to apply.

        Returns:
            The discounted price if applicable, None otherwise.
        """
        if self.active and self.is_valid():
            percentage_discount = self.discount_percentage
            discount_amount = price * Decimal(percentage_discount / 100)
            discounted_price = price - round(discount_amount, 2)
            return discounted_price
        return price


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
    name = models.CharField(max_length=50, unique=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    description = models.TextField()
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True)
    image_url = models.URLField()
    in_stock = models.PositiveIntegerField()
    quantity_sold = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    label = models.CharField(max_length=50, null=True, blank=True)
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, null=True, blank=True)
    shipping_fee = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
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

    user = models.ForeignKey(User, on_delete=models.SET(get_sentinel_user))
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    review = models.TextField()
    image_url = models.URLField(null=True, blank=True)
    rating = models.IntegerField(choices=Ratings.choices, default=0)

    class Meta:
        get_latest_by = "created"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.product.update_rating()
        
    def __str__(self):
        return f"Review of {self.product.name} by {self.user.get_full_name()}"