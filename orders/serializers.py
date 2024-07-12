from decimal import Decimal as D
from rest_framework import serializers

from customers.models import Address
from customers.serializers import AddressSerializer, SimpleCustomerSerializer
from catalogue.serializers import SimpleProductSerializer

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):

    product = SimpleProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OrderItem
        exclude = ["order"]
        extra_kwargs = {"unit_price": {"required": False}}

    def get_subtotal(self, obj):
        return f"${obj.calculate_subtotal()}"


class OrderSerializer(serializers.ModelSerializer):

    address = AddressSerializer()
    customer = SimpleCustomerSerializer()
    items = OrderItemSerializer(many=True, required=False)
    url = serializers.HyperlinkedIdentityField(view_name="order_detail")
    total_discount = serializers.SerializerMethodField(read_only=True)
    subtotal = serializers.SerializerMethodField(read_only=True)
    shipping = serializers.SerializerMethodField(read_only=True)
    total = serializers.SerializerMethodField(read_only=True)

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
            "total_discount",
            "subtotal",
            "shipping",
            "total",
            "status",
        ]

    def get_subtotal(self, obj):
        return sum(item.calculate_subtotal() for item in obj.items.all())

    def get_total_discount(self, obj):
        total = 0
        for item in obj.items.all():
            if item.discounted_price:
                total += (item.unit_price - item.discounted_price) * item.quantity
            if item.discounted_shipping:
                total += item.shipping_fee - item.discounted_shipping
        return total

    def get_shipping(self, obj):
        return float(obj.total_shipping_fee())

    def get_total(self, obj):
        return float(obj.total_cost())

    def update(self, instance, validated_data):
        data = validated_data.get("address")
        try:
            address, created = Address.objects.get_or_create(**data)
        except Address.MultipleObjectsReturned:
            address = Address.objects.filter(**data).first()
        instance.address = address
        instance.save()
        return instance
