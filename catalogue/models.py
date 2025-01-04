import os
import magic

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from customers.models import get_sentinel_user
from stores.models import Store


# Create your models here.
User = get_user_model()


class Timestamp(models.Model):
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


class Product(Timestamp):
    """
    Model representing a product.
    """

    name = models.CharField(max_length=255, unique=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING)
    description = models.TextField()
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True)
    in_stock = models.PositiveIntegerField()
    quantity_sold = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    available = models.BooleanField(default=False)
    rating = models.FloatField(null=True, blank=True)

    objects = models.Manager()

    class Meta:
        ordering = ["-quantity_sold", "-rating"]
        index = [models.Index(fields=["category", "available"])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.available = self.in_stock > 0
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
        results = self.reviews.aggregate(sum=models.Sum("rating"), count=models.Count("id"))
        rating_sum, reviews_count = results.values()
        return rating_sum / reviews_count if reviews_count else None


class ProductMedia(Timestamp):
    """
    Handles media files (images/videos) for products with automatic validation
    """

    ALLOWED_IMAGE_TYPES = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }

    ALLOWED_VIDEO_TYPES = {"video/mp4": ".mp4", "video/webm": ".webm"}

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="media")
    file = models.FileField(upload_to="products/%Y/%m/")
    is_primary = models.BooleanField(default=False, help_text="Set as primary media for product")

    class Meta:
        ordering = ["-is_primary", "-created_at"]
        verbose_name_plural = "product media"

    def __str__(self):
        return f"{self.product.name} - {'Primary' if self.is_primary else 'Secondary'}"

    def clean(self):
        if not self.file:
            return

        # Get file mime type
        file_type = magic.from_buffer(self.file.read(), mime=True)

        # Reset file pointer after reading
        self.file.seek(0)

        # Validate file type
        if file_type in self.ALLOWED_IMAGE_TYPES:
            self.type = "image"
            allowed_extensions = self.ALLOWED_IMAGE_TYPES
        elif file_type in self.ALLOWED_VIDEO_TYPES:
            self.type = "video"
            allowed_extensions = self.ALLOWED_VIDEO_TYPES
        else:
            raise ValidationError(
                f"Unsupported file type. Allowed types are: "
                f"{list(self.ALLOWED_IMAGE_TYPES.values()) + list(self.ALLOWED_VIDEO_TYPES.values())}"
            )

        # Validate file extension matches mime type
        file_extension = os.path.splitext(self.file.name)[1].lower()
        if file_extension != allowed_extensions[file_type]:
            raise ValidationError(
                f"File extension does not match its content. "
                f"Expected {allowed_extensions[file_type]} for {file_type}"
            )

    def save(self, *args, **kwargs):
        # If this is being set as primary, unset any existing primary
        if self.is_primary:
            ProductMedia.objects.filter(product=self.product, is_primary=True).update(is_primary=False)

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_image(self):
        return os.path.splitext(self.file.name)[1].lower() in self.ALLOWED_IMAGE_TYPES.values()

    @property
    def is_video(self):
        return os.path.splitext(self.file.name)[1].lower() in self.ALLOWED_VIDEO_TYPES.values()

    def get_file_size(self):
        return round(self.file.size / (1024 * 1024), 2)


class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="attributes")
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "product attribute"
        unique_together = ("product", "name")

    def attribute_values(self):
        return list(self.value_set.values_list("value", flat=True))


class ProductAttributeValue(models.Model):
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name="value_set")
    value = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return self.value

    def save(self, *args, **kwargs):
        self.is_default = self.attribute.value_set.count() < 1
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "attribute value"
        verbose_name_plural = "attribute values"
        unique_together = ("attribute", "value")
        indexes = [
            models.Index(fields=["attribute", "is_active"]),
        ]


class Review(Timestamp):
    "Model representing a review for a product."

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
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    review_text = models.TextField()
    rating = models.IntegerField(choices=Ratings.choices)
    sentiment = models.CharField(max_length=50, null=True, choices=SENTIMENT_TYPES)
    sentiment_score = models.FloatField(null=True)

    class Meta:
        get_latest_by = "created"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.product.update_rating()

    def __str__(self):
        return f"Review by {self.user}"


class ReviewImage(models.Model):
    review = models.ForeignKey(Review, on_delete=models.DO_NOTHING, related_name="images")
    image = models.ImageField(upload_to="reviews/")
    is_primary = models.BooleanField(default=False)
