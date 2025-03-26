import os
from decimal import Decimal as D

import magic
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from customers.models import get_sentinel_user
from discount.models import Offer
from stores.models import Store

from .abstract import BaseModel
from .sentiment import analyze

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


class Product(BaseModel):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING)
    description = models.TextField()
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)
    specs = models.JSONField(null=True, blank=True)
    is_standalone = models.BooleanField(
        default=True,
        help_text=(
            "If True, this product can be sold directly. Else, it acts as a template and only its variants can be sold"
        ),
    )

    # Stock status fields
    total_stock_level = models.PositiveIntegerField()
    total_sold = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created", "-total_sold", "-rating"]
        indexes = [models.Index(fields=["category", "is_active"])]

    def __str__(self):
        return self.name

    @property
    def has_variants(self):
        return self.variants.exists()

    @property
    def is_low_stock(self):
        return self.total_stock_level < 10

    def update_stock_status(self):
        # Use aggregation for efficiency
        results = self.variants.aggregate(
            total_stock=models.Sum("stock_level"), total_sold=models.Sum("quantity_sold")
        )
        self.total_stock_level = results["total_stock"] or 0
        self.total_sold = results["total_sold"] or 0
        self.is_active = self.total_stock_level > 0
        self.save(update_fields=["total_stock_level", "total_sold", "is_active"])

    def get_active_offers(self):
        """
        Get all active offers applicable to this product, either directly or through its category.
        """
        return Offer.active_objects.filter(
            models.Q(
                conditions__condition_type="specific_products",
                conditions__eligible_products=self,
            )
            | models.Q(
                conditions__condition_type="specific_categories",
                conditions__eligible_categories=self.category,
            ),
            offer_type="product",
            requires_voucher=False,
            total_discount_offered__lt=models.F("max_discount_allowed"),
        ).distinct()

    def find_best_offer(self, customer):
        """
        Finds the best applicable offer
        Returns the offer that gives the highest discount.
        """
        active_offers = self.get_active_offers()
        offer_discounts = []
        original_price = self.base_price

        for offer in active_offers:
            is_valid, _ = offer.satisfies_conditions(product=self, customer=customer)

            if is_valid:
                discount_amount = offer.get_discount_amount(original_price)
                offer_discounts.append((offer, discount_amount))

        # Sort by discount amount and get the best offer
        if offer_discounts:
            best_offer, _ = max(offer_discounts, key=lambda x: x[1])
            return best_offer

        return None


class Attribute(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_global = models.BooleanField(default=False)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, null=True, blank=True, related_name="attributes"
    )

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if not self.is_global and not self.product:
            raise ValidationError("Product-specific attribute must be assigned to a product")
        if self.is_global and self.product:
            self.product = None  # Global attributes can't belong to a product


class ProductVariant(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField("SKU", max_length=20, unique=True, db_index=True)
    is_default = models.BooleanField(
        default=False, help_text="Automatically created variant for standalone products"
    )
    price_adjustment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=D("0.0"),
        help_text="Additional amount to the product's base price",
    )
    stock_level = models.PositiveIntegerField()
    attributes = models.ManyToManyField(Attribute, through="catalogue.VariantAttribute")
    quantity_sold = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="media/variants", null=True, blank=True)

    class Meta:
        ordering = ("-quantity_sold",)
        indexes = [models.Index(fields=("product", "is_active"))]
        constraints = [
            models.UniqueConstraint(
                fields=["product"],
                condition=models.Q(is_default=True),
                name="unique_default_variant",
            ),
            models.UniqueConstraint(
                fields=["product", "sku"], name="unique_variant_sku_per_product"
            ),
        ]

    def __str__(self):
        attributes = self.variantattribute_set.all()
        return (
            ", ".join(f"{attr.attribute}: {attr.value}" for attr in attributes)
            if attributes
            else "Default"
        )

    @property
    def actual_price(self):
        return self.product.base_price + self.price_adjustment

    def _get_discount_price(self, customer):
        # Find and apply best price from the product's offers for the customer
        product_offer = self.product.find_best_offer(customer)
        if product_offer:
            return product_offer.apply_discount(self.actual_price)
        return 0

    def get_final_price(self, customer=None):
        discount_price = None if not customer else self._get_discount_price(customer)
        return discount_price if discount_price else self.actual_price

    def clean(self):
        super().clean()
        if hasattr(self, "product") and self.product is not None:
            if self.product.is_standalone and self.product.has_variants:
                raise ValidationError(
                    "Standalone products can only have a single default variant"
                )


class VariantAttribute(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    class Meta:
        unique_together = ("variant", "attribute")

    def __str__(self):
        return f"{self.attribute}: {self.value}"

    def clean(self):
        if not self.attribute.is_global and self.variant.product != self.attribute.product:
            raise ValidationError(
                f"Attribute {self.attribute.name} is specific to {self.attribute.product.name}"
            )

        existing = (
            self._meta.model.objects.filter(
                variant__product=self.variant.product,
                attribute=self.attribute,
                value=self.value,
            )
            .exclude(pk=self.id)
            .exists()
        )
        if existing:
            raise ValidationError("This attribute combination already exists")


ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

ALLOWED_VIDEO_TYPES = {"video/mp4": ".mp4", "video/webm": ".webm"}


class ProductMedia(BaseModel):
    """
    Handles media files (images/videos) for products with validation
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="media")
    file = models.FileField(upload_to="products/%Y/%m/")
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Alternative text for media (for accessibility)",
    )
    is_primary = models.BooleanField(
        default=False, help_text="Set as primary media for product"
    )

    class Meta:
        verbose_name_plural = "product media"
        ordering = ["-is_primary", "created"]

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
        if file_type in ALLOWED_IMAGE_TYPES:
            self.type = "image"
            allowed_extensions = ALLOWED_IMAGE_TYPES
        elif file_type in ALLOWED_VIDEO_TYPES:
            self.type = "video"
            allowed_extensions = ALLOWED_VIDEO_TYPES
        else:
            raise ValidationError(
                f"Unsupported file type. Allowed types are: "
                f"{list(ALLOWED_IMAGE_TYPES.values()) + list(ALLOWED_VIDEO_TYPES.values())}"
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
            ProductMedia.objects.filter(product=self.product, is_primary=True).update(
                is_primary=False
            )

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_image(self):
        return os.path.splitext(self.file.name)[1].lower() in ALLOWED_IMAGE_TYPES.values()

    @property
    def is_video(self):
        return os.path.splitext(self.file.name)[1].lower() in ALLOWED_VIDEO_TYPES.values()

    def get_file_size(self):
        return round(self.file.size / (1024 * 1024), 2)


class Review(BaseModel):
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
    sentiment = models.CharField(max_length=50, null=True, choices=SENTIMENT_TYPES, blank=True)
    sentiment_score = models.FloatField(null=True, blank=True)
    is_helpful = models.BooleanField(default=False, null=True, blank=True)

    class Meta:
        get_latest_by = "created"

    def save(self, *args, **kwargs):
        self.sentiment_score, self.sentiment = analyze(self.review_text)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Review by {self.user}"


class ReviewImage(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="reviews/")
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Alternative text for image (for accessibility)",
    )
    is_primary = models.BooleanField(
        default=False, help_text="Set as the main image for this review"
    )

    class Meta:
        ordering = ["-is_primary", "id"]

    def __str__(self):
        return f"Image for review {self.review.id} - {'Primary' if self.is_primary else 'Secondary'}"

    def clean(self):
        if not self.image:
            return

        try:
            file_type = magic.from_buffer(self.image.read(2048), mime=True)  # Read first 2KB
        except Exception as e:
            raise ValidationError(f"Could not determine file type: {e}")
        finally:
            self.image.seek(0)

        if file_type not in ALLOWED_IMAGE_TYPES:
            raise ValidationError(
                f"Unsupported image type. Allowed types are: {list(ALLOWED_IMAGE_TYPES.values())}"
            )

        # Validate file extension matches mime type
        file_extension = os.path.splitext(self.image.name)[1].lower()
        if file_extension != ALLOWED_IMAGE_TYPES[file_type]:
            raise ValidationError(
                f"File extension '{file_extension}' does not match its content type '{file_type}'. "
                f"Expected {ALLOWED_IMAGE_TYPES[file_type]}."
            )

    def save(self, *args, **kwargs):
        # If this is being set as primary, unset any existing primary for this review
        if self.is_primary:
            self.__class__.objects.filter(review=self.review, is_primary=True).exclude(
                pk=self.pk
            ).update(is_primary=False)

        self.full_clean()
        super().save(*args, **kwargs)

    def get_file_size(self):
        try:
            return round(self.image.size / (1024 * 1024), 2)  # Size in MB
        except OSError:
            return 0  # Handle cases where file might not exist
