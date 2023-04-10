from rest_framework import serializers

from .models import Product, Review


class ProductCreateUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = [
            "name",
            "category",
            "description",
            "image_url",
            "stock",
            "price",
            "label",
        ]

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.category = validated_data.get("category", instance.category)
        instance.description = validated_data.get("description", instance.description)
        instance.image_url = validated_data.get("image_url", instance.image_url)
        instance.stock = validated_data.get("stock", instance.stock)
        instance.label = validated_data.get("label", instance.label)
        instance.price = validated_data.get("price", instance.price)
        instance.save()
        return instance


class ProductReviewSerializer(serializers.ModelSerializer):

    user = serializers.StringRelatedField()

    class Meta:
        model = Review
        fields = ["id", "user", "review", "image_url", "created"]


class ProductsListSerializer(serializers.ModelSerializer):

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
            "available",
            "stock",
            "price",
            "sold",
            "label",
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
