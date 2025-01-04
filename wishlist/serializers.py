from rest_framework import serializers
from drf_writable_nested.serializers import WritableNestedModelSerializer

from .models import Wishlist, WishlistItem


class WishlistSerializer(WritableNestedModelSerializer):

    items = serializers.StringRelatedField(many=True)
    owner = serializers.StringRelatedField()

    class Meta:
        model = Wishlist
        fields = "__all__"

    def create(self, validated_data):
        return Wishlist.objects.create(
            name=validated_data["name"],
            owner=self.context["owner"],
            audience=validated_data["audience"],
            note=validated_data.get("note"),
        )
