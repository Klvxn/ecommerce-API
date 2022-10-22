from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):

    category = serializers.StringRelatedField()
    
    class Meta:
        model = Product
        fields = [
            "name",
            "category",
            "description",
            "image_url",
            "stock",
            "price",
            "available",
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
