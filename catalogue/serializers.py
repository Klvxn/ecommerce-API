from rest_framework import serializers

from discount.serializers import OfferSerializer

from .models import (
    Category,
    Product,
    ProductMedia,
    ProductVariant,
    Review,
    ReviewImage,
    VariantAttribute,
)


class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        exclude = ["review"]


class ProductReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    reviewimage_set = ReviewImageSerializer(many=True)

    class Meta:
        model = Review
        exclude = ["product"]


class ProductMediaSerializer(serializers.ModelSerializer):
    file_size = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()

    class Meta:
        model = ProductMedia
        fields = ["id", "file", "is_primary", "file_size", "file_type"]
        read_only_fields = ["file_size", "file_type"]

    def get_file_size(self, obj):
        return obj.get_file_size()

    def get_file_type(self, obj):
        if obj.is_image:
            return "image"
        elif obj.is_video:
            return "video"
        return "unknown"

    def validate_file(self, value):
        # Validate file size (e.g., 10MB limit)
        if value.size > 10 * 1024 * 1024:  # 10MB
            raise serializers.ValidationError("File size cannot exceed 10MB")
        return value


class VariantAttributeSerializer(serializers.ModelSerializer):
    attribute = serializers.StringRelatedField()

    class Meta:
        model = VariantAttribute
        exclude = ["variant", "id"]


class ProductVariantSerializer(serializers.ModelSerializer):
    # allow_null: for standalone products with no attributes
    attributes = VariantAttributeSerializer(many=True, allow_null=True)

    class Meta:
        model = ProductVariant
        exclude = ["product"]


class ProductListSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    store = serializers.HyperlinkedRelatedField(
        view_name="store-detail", lookup_field="slug", read_only=True
    )
    media = ProductMediaSerializer(many=True)
    active_offer = serializers.SerializerMethodField()
    base_price = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", 
            "name", 
            "category", 
            "store",
            "description",
            "is_active",
            "base_price",
            "active_offer",
            "discounted_price",
            "is_standalone",
            "media", 
            "created", 
            "updated",
            "total_stock_level",
            "total_sold"
        ]

    def get_base_price(self, obj):
        if obj.variants.exists():
            variant = obj.variants.order_by("price_adjustment").first()
            return variant.actual_price
        return obj.base_price

    def get_active_offer(self, obj):
        request = self.context["request"]
        active_offer = obj.find_best_offer(customer=request.user)
        if active_offer:
            return OfferSerializer(active_offer).data
        return None

    def get_discounted_price(self, obj):
        request = self.context["request"]
        best_offer = obj.find_best_offer(customer=request.user)
        if not best_offer:
            return None
        discount_amount = best_offer.get_discount_amount(self.get_base_price(obj))
        return self.get_base_price(obj) - discount_amount

    def to_representation(self, instance):
        data = super().to_representation(instance)
        discount = data["discounted_price"]
        base_price = data["base_price"]
        if discount:
            data["savings"] = max(base_price - discount, 0)
        return data


class ProductInstanceSerializer(ProductListSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "product" in self.context:
            self.product = self.context["product"]

    reviews = ProductReviewSerializer(many=True)
    variants = ProductVariantSerializer(many=True)

    class Meta:
        model = Product
        fields = "__all__"


class SimpleProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ["id", "name", "category"]


class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class CategoryInstanceSerializer(serializers.ModelSerializer):
    product_set = ProductListSerializer(many=True)

    class Meta:
        model = Category
        fields = "__all__"
