from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from catalogue.serializers import ProductListSerializer
from customers.serializers import AddressSerializer

from .models import Store


class StoreSerializer(WritableNestedModelSerializer):
    address = AddressSerializer()
    owner = serializers.StringRelatedField()

    class Meta:
        model = Store
        fields = [
            "id",
            "url",
            "name",
            "about",
            "is_active",
            "is_verified",
            "products_sold",
            "owner",
            "address",
            "followers",
        ]
        extra_kwargs = {"url": {"view_name": "store-detail", "lookup_field": "slug"}}
        read_only_fields = ["is_verified", "is_active", "products_sold", "followers"]

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.owner.is_vendor = True
        instance.owner.is_staff = True
        instance.save()
        return instance


class StoreInstanceSerializer(serializers.ModelSerializer):
    product_set = ProductListSerializer(many=True, required=False)

    class Meta:
        model = Store
        fields = StoreSerializer.Meta.fields + ["product_set"]
        extra_kwargs = {"url": {"view_name": "store-detail", "lookup_field": "slug"}}

