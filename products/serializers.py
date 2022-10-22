from rest_framework import serializers

from .models import Product, Review


class ReviewSerializer(serializers.ModelSerializer):

    user = serializers.StringRelatedField()

    class Meta:
        model = Review
        fields = ["user", "review"]


class ProductSerializer(serializers.ModelSerializer):

    category = serializers.StringRelatedField()
    reviews = ReviewSerializer(many=True, required=False)
    
    class Meta:
        model = Product
        fields = [
            "name",
            "category",
            "description",
            "image_url",
            "stock",
            "price",
            "reviews",
        ]


class SimpleProductSerializer(serializers.ModelSerializer):

    category = serializers.StringRelatedField()
    
    class Meta:
        model = Product
        fields = [
            "name",
            "category",
            "price",
        ]
