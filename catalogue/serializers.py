import json

from rest_framework import serializers

from .models import Product, Review


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


class CartSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(initial=1)
    attribute_values = serializers.JSONField()
