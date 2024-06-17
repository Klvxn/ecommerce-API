from rest_framework import serializers

from catalogue.serializers import ProductsListSerializer

from .models import Vendor


class VendorSerializer(serializers.ModelSerializer):

    total_products_sold = serializers.ReadOnlyField(source="get_total_products_sold")

    class Meta:
        model = Vendor
        fields = ["id", "url", "brand_name", "about", "total_products_sold", "customer"]
        extra_kwargs = {
            "url": {"lookup_field": "slug"}
        }


class VendorInstanceSerializer(serializers.HyperlinkedModelSerializer):

    product_set = ProductsListSerializer(many=True, required=False)
    total_products_sold = serializers.ReadOnlyField(source="get_total_products_sold")

    class Meta:
        model = Vendor
        fields = VendorSerializer.Meta.fields + ["product_set"]
        extra_kwargs = {
            "url": {"lookup_field": "slug"}
        }
