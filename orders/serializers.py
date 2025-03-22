from decimal import Decimal as D

from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from cart.cart import Cart
from catalogue.serializers import SimpleProductSerializer
from customers.models import Address
from customers.serializers import AddressSerializer, SimpleCustomerSerializer

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer(read_only=True)
    variant_sku = serializers.CharField(source="variant.sku", max_length=50)

    class Meta:
        model = OrderItem
        exclude = ["order", "variant"]
        read_only_fields = [
            "id",
            "product",
            "unit_price",
            "discount_amount",
            "total_price",
        ]

    def validate(self, attrs):
        """
        Validates price integrity and discount application:
        - Ensures discounts don't exceed unit prices
        - Verifies offers are active and properly applied
        - Confirms total_price calculations are accurate
        """
        offer = attrs.get("offer")
        unit_price = attrs.get("unit_price")
        discount_amount = attrs.get("discount_amount", D("0.0"))
        quantity = attrs.get("quantity", 1)

        # Calculate expected total price
        if unit_price:
            expected_total = unit_price * quantity

            # If there's a mismatch between provided total_price and calculated
            if "total_price" in attrs and attrs["total_price"] != expected_total:
                raise serializers.ValidationError(
                    f"Total price: {attrs['total_price']} doesn't match unit price × quantity ({expected_total})"
                )

        # Validate offer application if present
        if offer:
            # Check if offer is valid
            if offer.is_expired or not offer.is_active:
                raise serializers.ValidationError("The offer has expired and cannot be applied")

            # Ensure offer is properly applied for product-level offers
            if offer.for_product and discount_amount is not None and unit_price is not None:
                # Check if discount respects the max_discount_allowed
                if offer.total_discount_offered >= offer.max_discount_allowed:
                    raise serializers.ValidationError(
                        "This offer has reached its maximum allowed discount"
                    )

                # Validate the discount amount matches what the offer should apply
                expected_price = offer.apply_discount(unit_price)
                actual_price = unit_price - discount_amount
                if actual_price < expected_price:
                    raise serializers.ValidationError(
                        f"Invalid discount application. Price cannot be lower than {expected_price}"
                    )

        # Ensure discount cannot exceed unit price
        if discount_amount and discount_amount > unit_price:
            raise serializers.ValidationError("Discount amount cannot exceed unit price")

        return super().validate(attrs)


class OrderSerializer(WritableNestedModelSerializer):
    billing_address = AddressSerializer()
    customer = SimpleCustomerSerializer(read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="order_detail")
    items = OrderItemSerializer(many=True, required=False, read_only=True)
    shipping = serializers.SerializerMethodField(read_only=True, source="total_shipping")

    class Meta:
        model = Order
        fields = [
            "id",
            "url",
            "customer",
            "created",
            "updated",
            "billing_address",
            "items",
            "items_count",
            "savings_on_items",
            "status",
            "subtotal",
            "amount_saved",
            "shipping",
            "total_amount",
        ]
        read_only_fields = ["id", "items", "status"]

    def update(self, instance, validated_data):
        data = validated_data.get("billing_address")
        try:
            address, _ = Address.objects.get_or_create(**data, order=instance)
        except Address.MultipleObjectsReturned:
            address = Address.objects.filter(**data,  order=instance).first()
        instance.billing_address = address
        instance.save()
        return instance


class CheckoutSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=[("save_order", "Save order"), ("checkout", "Checkout")], write_only=True
    )
    billing_address = AddressSerializer(required=False, write_only=True)

    def create(self, validated_data):
        request = self.context["request"]
        cart = Cart(request)
        address = validated_data.get("billing_address")
        billing_address, _ = Address.objects.get_or_create(**address, customer=request.user)
        order = Order.create_from_cart(cart, billing_address)
        cart.clear(discounts_applied=True)
        return order

    def validate(self, attrs):
        request = self.context["request"]
        cart = Cart(request)
        if len(cart.cart_items) <= 0:
            raise serializers.ValidationError({"cart": "Can't create order from an empty"})
        return super().validate(attrs)
