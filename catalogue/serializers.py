from django.db.models import Count
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from .models import Product, ProductAttribute, ProductImage, Review, ReviewImage
from .vouchers.models import Voucher


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


class ProductAttrSerializer(serializers.ModelSerializer):

    value_set = serializers.StringRelatedField(many=True)

    class Meta:
        model = ProductAttribute
        fields = ["name", "value_set"]


class ProductImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductImage
        exclude = ["product"]


class ProductsListSerializer(serializers.ModelSerializer):

    category = serializers.StringRelatedField()
    store = serializers.HyperlinkedRelatedField(
        view_name="store-detail", lookup_field="slug", read_only=True
    )
    image_set = ProductImageSerializer(many=True)
    attributes = ProductAttrSerializer(many=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "store",
            "description",
            "image_set",
            "available",
            "attributes",
            "shipping_fee",
            "in_stock",
            "price",
            "quantity_sold",
            "rating"
        ]


class ProductInstanceSerializer(ProductsListSerializer):

    reviews = ProductReviewSerializer(many=True)

    class Meta:
        model = Product
        fields = ProductsListSerializer.Meta.fields + ["reviews"]


class SimpleProductSerializer(serializers.ModelSerializer):

    category = serializers.StringRelatedField()
    store = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ["id", "name", "category", "store"]


class AddToCartSerializer(serializers.Serializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "product_id" in self.context:
            self.product_id = self.context["product_id"]

    quantity = serializers.IntegerField(min_value=1)
    attribute_values = serializers.JSONField(initial={})
    discount_code = serializers.CharField(max_length=20, allow_blank=True)

    def validate_quantity(self, data):
        product = get_object_or_404(Product, pk=self.product_id)
        if data > product.in_stock:
            raise serializers.ValidationError(
                "The quantity cannot be more than product's stock"
            )
        return data

    def validate_discount_code(self, data):
        if data:
            voucher = Voucher.objects.filter(code=data.upper()).first()
            if not voucher or not voucher.within_validity_period():
                raise serializers.ValidationError("Invalid or expired voucher code")
        return data

    def validate_attribute_values(self, data):
        product = get_object_or_404(Product, pk=self.product_id)
        single_valued_attrs = product.attributes.annotate(count=Count("value_set")).filter(count=1)
        multi_valued_attrs = product.attributes.annotate(count=Count("value_set")).filter(count__gt=1)
        if single_valued_attrs:
            for attr in single_valued_attrs:
                data[attr.name] = attr.value_set.values_list("value", flat=True)[0]
        if not data and multi_valued_attrs:
            raise serializers.ValidationError(
                f"You must specify values for {[attr.name for attr in multi_valued_attrs]}"
            )
        if multi_valued_attrs:
            for attr in multi_valued_attrs:
                if attr.name not in data.keys():
                    raise serializers.ValidationError(
                        f"Missing value for multivalued attribute '{attr.name}'"
                    )
                if not attr.value_set.filter(value=data[attr.name]).exists():
                    raise serializers.ValidationError(
                        f"Invalid value '{data[attr.name]}' for attribute '{attr.name}'"
                    )
        return data
