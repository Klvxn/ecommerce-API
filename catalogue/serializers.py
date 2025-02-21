from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from .models import Category, Product, ProductMedia, ProductVariant, Review, ReviewImage, VariantAttribute
from discount.models import Offer
from discount.serializers import OfferSerializer


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
    variant_attributes = VariantAttributeSerializer(many=True)

    class Meta:
        model = ProductVariant
        exclude = ["product"]


class ProductListSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    store = serializers.HyperlinkedRelatedField(
        view_name="store-detail", lookup_field="slug", read_only=True
    )
    media = ProductMediaSerializer(many=True)

    class Meta:
        model = Product
        fields = "__all__"


class ProductInstanceSerializer(ProductListSerializer):
    reviews = ProductReviewSerializer(many=True)
    variants = ProductVariantSerializer(many=True)
    product_offers = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"

    def get_product_offers(self, obj):
        filtered_offers = Offer.objects.filter(target="Product")
        return OfferSerializer(filtered_offers, many=True).data


class SimpleProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    store = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ["id", "name", "category", "store"]


class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class CategoryInstanceSerializer(serializers.ModelSerializer):
    product_set = ProductListSerializer(many=True)

    class Meta:
        model = Category
        fields = "__all__"
