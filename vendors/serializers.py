from rest_framework import serializers

from products.serializers import ProductsSerializer

from .models import Vendor


class VendorSerializer(serializers.ModelSerializer):

    product_set = ProductsSerializer(many=True)

    class Meta:
        model = Vendor
        fields = ["brand_name", "product_set"]
