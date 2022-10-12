from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from customers.serializers import AddressSerializer
from products.serializers import ProductSerializer

from .models import Order, OrderItem


class OrderItemSerializer(WritableNestedModelSerializer):

    product = ProductSerializer()
    cost = serializers.ReadOnlyField(source="get_cost")

    class Meta:
        model = OrderItem
        fields = ["product", "quantity", "cost"]


class OrderSerializer(WritableNestedModelSerializer):

    address = AddressSerializer(required=False)
    customer = serializers.StringRelatedField()
    order_items = OrderItemSerializer(many=True, required=False)
    url = serializers.HyperlinkedIdentityField(view_name="order-detail")
    total_cost = serializers.ReadOnlyField(source="get_total_cost")

    class Meta:
        model = Order
        fields = [
            "id",
            "url",
            "customer",
            "created",
            "address",
            "order_items",
            "total_cost",
            "status",
        ]


class SimpleOrderItemSerializer(serializers.ModelSerializer):

    product = serializers.StringRelatedField()
    cost = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["product", "quantity", "cost"]

    def get_cost(self, obj):
        return f"{obj.get_cost()}"


class SimpleOrderSerializer(serializers.ModelSerializer):

    address = AddressSerializer(required=False)
    customer = serializers.StringRelatedField()
    order_items = SimpleOrderItemSerializer(many=True, required=False)
    total_cost = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "created",
            "address",
            "order_items",
            "total_cost",
            "status",
        ]

    def get_total_cost(self, obj):
        return f"{obj.get_total_cost()}"
