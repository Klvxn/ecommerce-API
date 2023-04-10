from rest_framework import serializers

from .models import Product, Review


class ProductReviewSerializer(serializers.ModelSerializer):

    user = serializers.StringRelatedField()

    class Meta:
        model = Review
        fields = ["id", "user", "review", "image_url", "created"]


class ProductsSerializer(serializers.ModelSerializer):

    category = serializers.StringRelatedField()
    price = serializers.SerializerMethodField(read_only=True)
    vendor = serializers.HyperlinkedRelatedField(
        view_name="vendor-detail", lookup_field="slug", read_only=True
    )
    
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "vendor",
            "description",
            "image_url",
            "stock",
            "price",
            "sold",
        ]

    def get_price(self, obj):
        return f"${obj.price}"


class ProductInstanceSerializer(ProductsSerializer):

    reviews = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ProductsSerializer.Meta.fields + ["reviews"]

    def get_reviews(self, obj):
        return obj.get_latest_reviews()


class SimpleProductSerializer(serializers.ModelSerializer):

    category = serializers.StringRelatedField()
    price = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "price",
        ]

    def get_price(self, obj):
        return f"${obj.price}"
