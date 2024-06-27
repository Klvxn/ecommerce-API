from rest_framework import serializers

from catalogue.serializers import ProductsListSerializer

from .models import Store


class StoreSerializer(serializers.ModelSerializer):

    products_sold = serializers.ReadOnlyField(source="get_products_sold")

    class Meta:
        model = Store
        fields = [
            "id", "url", "brand_name", "about", "products_sold", "owner", "followers"
        ]
        extra_kwargs = {
            "url": {"lookup_field": "slug"}
        }
        
    def create(self, validated_data):
        obj = super().create(validated_data)
        obj.owner.is_vendor = True
        obj.owner.is_staff = True
        obj.save()
        return obj


class StoreInstanceSerializer(serializers.HyperlinkedModelSerializer):

    product_set = ProductsListSerializer(many=True, required=False)
    products_sold = serializers.ReadOnlyField(source="get_products_sold")

    class Meta:
        model = Store
        fields = StoreSerializer.Meta.fields + ["product_set"]
        extra_kwargs = {
            "url": {"lookup_field": "slug"}
        }
