from decimal import Decimal

from rest_framework import serializers

from catalogue.serializers import SimpleProductSerializer
from customers.models import Address
from customers.serializers import AddressSerializer, SimpleCustomerSerializer

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        exclude = ["order"]
        extra_kwargs = {"unit_price": {"required": False}}

    def validate(self, attrs):
        """
        Validate that discounted prices are correctly applied according to offer rules.
        """
        offer = attrs.get("offer")
        unit_price = attrs.get("unit_price")
        discounted_price = attrs.get("discounted_price")
        shipping_fee = attrs.get("shipping_fee")
        discounted_shipping = attrs.get("discounted_shipping")

        if offer:
            # Validate offer hasn't expired
            if offer.has_expired:
                raise serializers.ValidationError("The offer has expired and cannot be applied")

            # Validate discount application based on offer target
            if offer.for_product and discounted_price is not None:
                expected_price = offer.apply_discount(unit_price)
                if discounted_price < expected_price:
                    raise serializers.ValidationError(
                        f"Invalid discount application. Price cannot be lower than {expected_price}"
                    )

            elif offer.for_shipping and discounted_shipping is not None:
                if offer.discount_type == offer.FREE_SHIPPING:
                    if discounted_shipping != Decimal("0.00"):
                        raise serializers.ValidationError(
                            "Free shipping offer must set shipping cost to 0"
                        )
                else:
                    expected_shipping = offer.apply_discount(shipping_fee)
                    if discounted_shipping < expected_shipping:
                        raise serializers.ValidationError(
                            f"Invalid shipping discount. Cannot be lower than {expected_shipping}"
                        )

        # General validation for discount values
        if discounted_price is not None and discounted_price > unit_price:
            raise serializers.ValidationError("Discounted price cannot be higher than unit price")

        if discounted_shipping is not None and discounted_shipping > shipping_fee:
            raise serializers.ValidationError(
                "Discounted shipping cannot be higher than original shipping fee"
            )

        return super().validate(attrs)


class OrderSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    customer = SimpleCustomerSerializer()
    url = serializers.HyperlinkedIdentityField(view_name="order_detail")
    items = OrderItemSerializer(many=True, required=False)
    total_discount = serializers.SerializerMethodField(read_only=True)
    subtotal = serializers.SerializerMethodField(read_only=True)
    shipping = serializers.SerializerMethodField(read_only=True)
    savings = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "url",
            "customer",
            "created",
            "updated",
            "address",
            "items",
            "items_count",
            "savings",
            "status",
            "subtotal",
            "shipping",
            "total_amount",
        ]

    def get_subtotal(self, obj):
        return float(obj.subtotal())

    def get_savings(self, obj):
        return sum(item.savings for item in obj.items.all())

    def get_shipping(self, obj):
        return float(obj.total_shipping())

    def update(self, instance, validated_data):
        data = validated_data.get("address")
        try:
            address, created = Address.objects.get_or_create(**data)
        except Address.MultipleObjectsReturned:
            address = Address.objects.filter(**data).first()
        instance.address = address
        instance.save()
        return instance
