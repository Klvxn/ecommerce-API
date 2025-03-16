from django.utils.crypto import secrets
from rest_framework import serializers

from catalogue.models import Product
from catalogue.serializers import SimpleProductSerializer

from .models import Wishlist, WishlistItem


class WishlistItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.active_objects.all(), write_only=True
    )

    class Meta:
        model = WishlistItem
        fields = ["id", "product", "added_at", "product_id"]
        read_only_fields = ["added_at", "product"]
        write_only_fields = ["product_id"]

    def validate(self, attrs):
        product_id = attrs["product_id"]
        try:
            product = Product.active_objects.get(id=product_id)
            attrs["product"] = product
            return attrs
        except Product.DoesNotExist:
            return serializers.ValidationError({"product_id": "Product not found"})


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)
    owner = serializers.StringRelatedField()
    sharing_url = serializers.ReadOnlyField(source="get_sharing_url")

    class Meta:
        model = Wishlist
        fields = [
            "id",
            "name",
            "owner",
            "audience",
            "note",
            "items",
            "items_count",
            "sharing_url",
            "created",
            "updated",
        ]

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.note = validated_data.get("note", instance.note)

        new_audience = validated_data.get("audience")
        if new_audience and new_audience != instance.audience:
            instance.audience = new_audience
            # Generate sharing token if changing to shared visibility
            if new_audience == "shared" and not instance.sharing_token:
                instance.sharing_token = secrets.token_urlsafe(32)

        instance.save()
        return instance

    def validate_name(self, value):
        owner = self.context.get("owner")

        if not self.instance:  # Creating new wishlist
            if Wishlist.objects.filter(owner=owner, name=value).exists():
                raise serializers.ValidationError("You already have a wishlist with this name")

        else:  # Updating existing wishlist
            if (
                Wishlist.objects.filter(owner=owner, name=value)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError(
                    "You already have another wishlist with this name"
                )

        return value
