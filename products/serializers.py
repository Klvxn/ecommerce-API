from rest_framework import serializers

from .models import Product, Review


class ReviewSerializer(serializers.ModelSerializer):

    user = serializers.StringRelatedField()

    class Meta:
        model = Review
        fields = ["user", "review"]


class ProductsSerializer(serializers.ModelSerializer):

    category = serializers.StringRelatedField()
    vendor = serializers.HyperlinkedRelatedField(view_name="vendor", lookup_field="slug", read_only=True)

    class Meta:
        model = Product
        fields = [
            "name",
            "category",
            "vendor",
            "description",
            "image_url",
            "stock",
            "price",
        ]


class ProductInstanceSerializer(serializers.ModelSerializer):

    reviews = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ProductsSerializer.Meta.fields + ["reviews"]

    def get_reviews(self, obj):
        return obj.get_latest_reviews()


class SimpleProductSerializer(serializers.ModelSerializer):

    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = [
            "name",
            "category",
            "price",
        ]
