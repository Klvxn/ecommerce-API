from rest_framework import serializers

from products.serializers import ProductsSerializer

from .models import Vendor


class VendorSerializer(serializers.ModelSerializer):

    product_set = ProductsSerializer(many=True, required=False)
    total_products_sold = serializers.ReadOnlyField(source="get_total_products_sold")

    class Meta:
        model = Vendor
        fields = ["brand_name", "about", "product_set", "total_products_sold"]
