import os

import magic
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from customers.models import get_sentinel_user
from discount.models import Offer
from stores.models import Store

from .abstract import Timestamp

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


class Product(Timestamp):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING)
    description = models.TextField()
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)
    is_standalone = models.BooleanField(
        default=True,
        help_text="Does/Will this product have variants that inherits its properties?",
    )

    # Stock status fields
    total_stock_level = models.PositiveIntegerField()
    total_sold = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ["-total_sold", "-rating"]
        indexes = [models.Index(fields=["category", "is_available"])]

    def __str__(self):
        return self.name

    @property
    def has_variants(self):
        return not self.is_standalone and self.variants.exists()

    def update_stock_status(self):
        variants = self.variants.all()
        self.total_stock_level = sum(variant.stock_level for variant in variants)
        self.total_sold = sum(variant.quantity_sold for variant in variants)
        self.is_available = self.total_stock_level > 0
        self.save()

    def update_rating(self):
        self.rating = self.calculate_rating()
        self.save()

    def calculate_rating(self):
        results = self.reviews.aggregate(sum=models.Sum("rating"), count=models.Count("id"))
        rating_sum, reviews_count = results.values()
        return rating_sum / reviews_count if reviews_count else None

    def get_active_offers(self):
       # Get all active offers applicable to this product, either directly or through its category.
        active_offers = Offer.objects.filter(
            models.Q(
                conditions__condition_type="specific_products",
                conditions__eligible_products=self,
            )
            | models.Q(
                conditions__condition_type="specific_categories",
                conditions__eligible_categories=self.category,
            ),
            target="Product",
            requires_voucher=False,
            is_active=True,
        )
        return active_offers

    def find_best_offer(self, customer):
        """
        Finds the best applicable offer
        Returns the offer that gives the highest discount.
        """
        active_offers = self.get_active_offers()

        # Calculate the actual discount amount for each offer
        offer_discounts = []
        original_price = self.base_price

        for offer in active_offers:
            is_valid, _ = offer.satisfies_conditions(product=self, customer=customer)

            if is_valid:
                discounted_price = offer.apply_discount(original_price)
                discount_amount = original_price - discounted_price
                offer_discounts.append((offer, discount_amount))

        # Sort by discount amount and get the best offer
        if offer_discounts:
            best_offer, _ = max(offer_discounts, key=lambda x: x[1])
            return best_offer

        return None


# Common attributes like colour, size, serve as Global attributes
# as they are reusable across products
class Attribute(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="attributes")
    attribute = models.ForeignKey(Attribute, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)  # for product-specific attributes

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "product attribute"
        unique_together = ("product", "name")


class ProductVariant(Timestamp):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField("SKU", max_length=20, unique=True, db_index=True)
    is_default = models.BooleanField(default=False)
    price_adjustment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        help_text="Amount to add to the product's base price",
    )
    is_active = models.BooleanField(default=True)
    stock_level = models.PositiveIntegerField()
    quantity_sold = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("-quantity_sold",)
        unique_together = ("sku", "product")
        indexes = [models.Index(fields=("product", "is_active"))]

    def __str__(self):
        attriutes = self.attributes.all()
        variant_desc = " - ".join(f"{attr.attribute.name}: {attr.value}" for attr in attriutes)
        return f"{self.product.name} ({variant_desc})"

    @property
    def actual_price(self):
        return self.product.base_price + self.price_adjustment

    def get_discount_price(self, customer):
        # Find and apply best price from the product's offers for the customer 
        product_offer = self.product.find_best_offer(customer)
        if product_offer:
            return product_offer.apply_discount(self.actual_price)
        return 0

    def get_final_price(self, customer=None):
        discount_price = None if not customer else self.get_discount_price(customer)  
        return discount_price if discount_price else self.actual_price

    def clean(self):
        super().clean()
        if hasattr(self, "product") and self.product is not None:
            if self.product.is_standalone and not self.is_default:
                raise ValidationError("Standalone products can only have a single default variant")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.product.update_stock_status()


class VariantAttribute(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="attributes")
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"Variant attribute for {self.variant}"

    class Meta:
        unique_together = ("variant", "attribute")


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


class Review(Timestamp):
    class Ratings(models.IntegerChoices):
        VERY_BAD = 1, "Very Bad"
        UNSATISFIED = 2, "Unsatisfied"
        JUST_THERE = 3, "Just There"
        SATISFIED = 4, "Satisfied"
        VERY_SATISFIED = 5, "Very Satisfied"

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
