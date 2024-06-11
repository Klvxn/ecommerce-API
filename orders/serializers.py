from rest_framework import serializers

from customers.models import Address
from customers.serializers import AddressSerializer
from products.serializers import SimpleProductSerializer

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):

    product = SimpleProductSerializer()
    cost = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["product", "quantity", "unit_price", "discounted_price", "cost"]

    def get_cost(self, obj):
        return f"${obj.calculate_cost()}"


class OrderSerializer(serializers.ModelSerializer):

    address = AddressSerializer()
    customer = serializers.StringRelatedField()
    order_items = OrderItemSerializer(many=True, required=False)
    url = serializers.HyperlinkedIdentityField(view_name="order-detail")
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
            "order_items",
            "discount",
            "total_shipping",
            "total_cost",
            "status",
        ]

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
    cost = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["product", "quantity", "cost"]

    def get_cost(self, obj):
        return f"${obj.calculate_cost()}"


class SimpleOrderSerializer(serializers.ModelSerializer):

    address = AddressSerializer(required=False)
    customer = serializers.StringRelatedField()
    order_items = SimpleOrderItemSerializer(many=True, required=False)
    total_cost = serializers.SerializerMethodField(read_only=True)

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
        return f"${obj.total_cost()}"
