from django.db.models import Count
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from .models import Product, Review
from .vouchers.models import Voucher


class ProductReviewSerializer(serializers.ModelSerializer):

    user = serializers.StringRelatedField()

    class Meta:
        model = Review
        fields = ["id", "user", "review", "image_url", "rating", "created"]


class ProductsListSerializer(serializers.ModelSerializer):

    category = serializers.StringRelatedField()
    price = serializers.SerializerMethodField(read_only=True)
    store = serializers.HyperlinkedRelatedField(
        view_name="store-detail", lookup_field="slug", read_only=True
    )
    attributes = serializers.StringRelatedField(many=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "store",
            "description",
            "image_url",
            "available",
            "attributes",
            "shipping_fee",
            "in_stock",
            "price",
            "quantity_sold",
            "rating"
        ]

    def get_price(self, obj):
        return f"${obj.price}"


class ProductInstanceSerializer(ProductsListSerializer):

    reviews = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ProductsListSerializer.Meta.fields + ["reviews"]

    def get_reviews(self, obj):
        return obj.get_latest_reviews()


class SimpleProductSerializer(serializers.ModelSerializer):

    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "rating",
        ]


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
            data = data.upper()
            voucher = Voucher.objects.filter(code=data).first()
            if not voucher or not voucher.within_validity_period():
                raise serializers.ValidationError("Invalid or expired voucher code")
        return data

    def validate_attribute_values(self, data):
        product = get_object_or_404(Product, pk=self.product_id)
        single_valued_attrs = product.attributes.annotate(count=Count("values")).filter(count=1)
        multi_valued_attrs = product.attributes.annotate(count=Count("values")).filter(count__gt=1)
        if single_valued_attrs:
            for attr in single_valued_attrs:
                data[attr.name] = attr.values.values_list('value', flat=True)[0]
        if not data:
            if multi_valued_attrs:
                raise serializers.ValidationError(
                    f"You must specify values for {[attr.name for attr in multi_valued_attrs]}"
                )
        if multi_valued_attrs:
            for attr in multi_valued_attrs:
                if attr.name not in data.keys():
                    raise serializers.ValidationError(
                        f"Missing value for multivalued attribute '{attr.name}'"
                    )
                if not attr.values.filter(value=data[attr.name]).exists():
                    raise serializers.ValidationError(
                        f"Invalid value '{data[attr.name]}' for attribute '{attr.name}'"
                    )
        return data
