from decimal import Decimal as D
from rest_framework import serializers

from customers.models import Address
from customers.serializers import AddressSerializer
from catalogue.serializers import SimpleProductSerializer

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):

    product = SimpleProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["product", "quantity", "unit_price", "discounted_price", "subtotal"]
        extra_kwargs = {"unit_price": {"required": False}}

    def get_subtotal(self, obj):
        return f"${obj.calculate_subtotal()}"


class OrderSerializer(serializers.ModelSerializer):

    address = AddressSerializer()
    customer = serializers.StringRelatedField()
    items = OrderItemSerializer(many=True, required=False)
    url = serializers.HyperlinkedIdentityField(view_name="order_detail")
    total_discount = serializers.SerializerMethodField(read_only=True)
    total_shipping = serializers.SerializerMethodField(read_only=True)
    total_cost = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "url",
            "customer",
            "created",
            "address",
            "items",
            "total_discount",
            "total_shipping",
            "total_cost",
            "status",
        ]

    def get_total_discount(self, obj):
        return str(
            sum(
                item.cost_at_original_price()
                for item in obj.items.all()
                if item.cost_at_discounted_price() > D(0.00)
            )
            - sum(item.cost_at_discounted_price() for item in obj.items.all())
        )

    def get_total_shipping(self, obj):
        return f"${obj.total_shipping_fee()}"

    def get_total_cost(self, obj):
        return f"${obj.total_cost()}"

    def update(self, instance, validated_data):
        data = validated_data.get("address")
        try:
            address, created = Address.objects.get_or_create(**data)
        except Address.MultipleObjectsReturned:
            address = Address.objects.filter(**data).first()
        instance.address = address
        instance.save()
        return instance


class SimpleOrderItemSerializer(serializers.ModelSerializer):

    product = serializers.StringRelatedField()
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["product", "quantity", "subtotal"]

    def get_subtotal(self, obj):
        return f"${obj.calculate_subtotal()}"


class SimpleOrderSerializer(serializers.ModelSerializer):

    address = AddressSerializer(required=False)
    customer = serializers.StringRelatedField()
    items = SimpleOrderItemSerializer(many=True, required=False)
    total_cost = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "created",
            "address",
            "items",
            "total_cost",
            "status",
        ]

    def get_total_cost(self, obj):
        return f"${obj.total_cost()}"
