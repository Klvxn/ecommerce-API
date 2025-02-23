from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from catalogue.models import Product, ProductVariant


class AddToCartSerializer(serializers.Serializer):
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     if "product_id" in self.context:
    #         self.product_id = self.context["product_id"]

    quantity = serializers.IntegerField(min_value=1)
    variant_sku = serializers.CharField(max_length=20)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    def validate_variant_sku(self, data):
        if not data:
            raise serializers.ValidationError("Variant SKU cannot be null")
        else:
            try:
                get_object_or_404(ProductVariant, sku=data)
                return data
            except:
                raise serializers.ValidationError("Invalid variant_sku")

    def validate(self, attrs):
        quantity = attrs["quantity"]
        sku = attrs["variant_sku"]
        variant = get_object_or_404(ProductVariant, sku=sku)
        if quantity > variant.stock_level:
            raise serializers.ValidationError("Selected quantity cannot be more than product's stock")
        return super().validate(attrs)
