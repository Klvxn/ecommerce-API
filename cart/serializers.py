from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from catalogue.models import ProductVariant


class AddCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)
    variant_sku = serializers.CharField(label="Variant SKU", max_length=20)

    def validate_variant_sku(self, data):
        if not ProductVariant.objects.filter(sku=data).exists():
            raise serializers.ValidationError("Invalid variant SKU")
        return data

    def validate(self, attrs):
        attrs = super().validate(attrs)
        quantity = attrs["quantity"]
        variant = get_object_or_404(ProductVariant, sku=attrs["variant_sku"])

        if not variant.is_active:
            raise serializers.ValidationError({"item_key": "Product is no longer availabe"})

        if quantity > variant.stock_level:
            raise serializers.ValidationError({
                "quantity": f"Requested quantity: ({quantity}) exceeds available stock: ({variant.stock_level}) for this variant"
            })
        attrs["variant"] = variant
        return attrs


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField()
    item_key = serializers.CharField(max_length=50)

    def validate_item_key(self, data):
        cart = self.context["cart"]
        if data not in cart.cart_items.keys():
            raise serializers.ValidationError("Invalid cart item key")
        return data

    def validate(self, attrs):
        cart = self.context["cart"]
        item_key = attrs["item_key"]
        quantity = attrs["quantity"]
        cart_item = cart.cart_items[item_key]
        try:
            variant = ProductVariant.objects.get(id=cart_item["variant_id"])
            if not variant.is_active:
                raise serializers.ValidationError({"item_key": "Product is no longer availabe"})

        except ProductVariant.DoesNotExist:
            raise serializers.ValidationError({"item_key": "Product variant no longer exists"})

        attrs = super().validate(attrs)
        if quantity > variant.stock_level:
            raise serializers.ValidationError({
                "quantity": f"Requested quantity: ({quantity}) exceeds available stock: ({variant.stock_level}) for this variant"
            })
        attrs["variant"] = variant
        return attrs
