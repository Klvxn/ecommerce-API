from rest_framework import serializers
from drf_writable_nested.serializers import WritableNestedModelSerializer

from .models import Wishlist, WishlistItem

class WishlistSerializer(WritableNestedModelSerializer):

    items = serializers.StringRelatedField(many=True)
    owner = serializers.StringRelatedField()

    class Meta:
        model = Wishlist
        fields = "__all__"


class WishlistItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = WishlistItem
        fields = "__all__"