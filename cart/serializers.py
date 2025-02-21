from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from catalogue.models import Product, ProductVariant


class AddToCartSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "product_id" in self.context:
            self.product_id = self.context["product_id"]

    quantity = serializers.IntegerField(min_value=1)
    variant_sku = serializers.CharField(max_length=20)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    def validate_variant_sku(self, data):
        if not data:
            raise serializers.ValidationError("Variant SKU cannot be null")
        else:
            try:
                get_object_or_404(ProductVariant, sku=data, product=self.product_id)
                return data
            except:
                raise serializers.ValidationError("Invalid variant_sku")

    def validate_product(self, product):
        if not product.is_standalone:
            raise serializers.ValidationError(
                "Parent product cannot be added to cart. Choose product variant"
            )
        return product

    def validate(self, attrs):
        quantity = attrs["quantity"]
        product = attrs["product"]
        if quantity > product.total_stock_level:
            raise serializers.ValidationError("Selected quantity cannot be more than product's stock")

        variant_sku = attrs.get("variant_sku")
        product_variant = ProductVariant.objects.filter(sku=variant_sku, product=product).first()
        if product_variant and quantity > product_variant.stock_level:
            raise serializers.ValidationError("Selected quantity cannot be more than product's stock")
        return super().validate(attrs)
