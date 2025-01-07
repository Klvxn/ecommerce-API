from django.utils.crypto import secrets
from rest_framework import serializers

from catalogue.serializers import SimpleProductSerializer
from .models import Wishlist, WishlistItem


class WishlistItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer(read_only=True)

    class Meta:
        model = WishlistItem
        fields = ["id", "product", "added_at"]


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)
    owner = serializers.StringRelatedField(read_only=True)
    absolute_url = serializers.SerializerMethodField()
    public_url = serializers.SerializerMethodField()
    sharing_url = serializers.SerializerMethodField()

    class Meta:
        model = Wishlist
        fields = [
            "id",
            "name",
            "owner",
            "audience",
            "note",
            "items",
            "absolute_url",
            "public_url",
            "sharing_url",
            "created_at",
            "updated_at",
        ]

    def get_absolute_url(self, obj):
        return obj.get_absolute_url()

    def get_public_url(self, obj):
        return obj.get_public_url()

    def get_sharing_url(self, obj):
        return obj.get_sharing_url()

    def create(self, validated_data):
        owner = self.context.get("owner")
        if not owner:
            raise serializers.ValidationError("Owner is required for wishlist creation")

        return Wishlist.objects.create(owner=owner, **validated_data)

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
            if Wishlist.objects.filter(owner=owner, name=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("You already have another wishlist with this name")
        return value
