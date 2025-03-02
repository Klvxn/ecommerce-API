from django.db import transaction
from django.shortcuts import redirect
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import reverse, status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from cart.cart import Cart
from customers.serializers import AddressSerializer
from discount.models import Offer, Voucher

from .models import Order, OrderItem
from .serializers import OrderItemSerializer, OrderSerializer


# Create your views here.
class OrderListView(GenericAPIView, LimitOffsetPagination):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    filterset_fields = ["status"]

    def get_queryset(self):
        queryset = Order.objects.filter(customer=self.request.user)
        queryset = self.filter_queryset(queryset)
        return queryset

    @swagger_auto_schema(
        operation_summary="Get all orders by a customer",
        manual_parameters=[openapi.Parameter("status", in_=openapi.IN_QUERY, type=openapi.TYPE_STRING)],
        responses={200: OrderSerializer(many=True)},
        tags=["Order"],
    )
    def get(self, request):
        orders = self.get_queryset()
        page = self.paginate_queryset(orders)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Create an order from user's cart items",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["action"],
            properties={
                "action": openapi.Schema(type=openapi.TYPE_STRING),
                "voucher_code": openapi.Schema(type=openapi.TYPE_STRING),
                "address": openapi.Schema(type=openapi.TYPE_OBJECT),
            },
            example={
                "action": "checkout",
                "voucher_code": "SAVE10",
                "address": {
                    "street_address": "123 Main St",
                    "postal_code": "12345",
                    "city": "Anytown",
                    "state": "CA",
                    "country": "Canada",
                },
            },
        ),
        responses={201: OrderSerializer, 400: "Bad request"},
        tags=["Order"],
    )
    def post(self, request):
        """
        Handle POST request to create an order from the user's cart.
        """
        action = request.data.get("action")
        voucher_code = request.data.get("voucher_code")
        shipping_address = request.data.get("address")
        cart = Cart(request)

        # Validate the action type
        if action not in ("checkout", "save_order"):
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure the user's cart is not empty
        if len(cart) <= 0:
            return Response(
                {"error": "Can't create an order. Your cart is empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            customer = request.user
            order = Order.objects.create(customer=customer)

            # Apply discount for a product if a voucher code is provided/applicable to the product
            if voucher_code and not order.apply_voucher_offer(voucher_code):
                return Response(
                    {"error": "Invalid/Expired voucher code"}, status=status.HTTP_400_BAD_REQUEST
                )

            #  A new shipping address is provided or use customer's address
            if not (shipping_address or customer.address):
                return Response(
                    {"error": "Shipping address was not provided"}, status=status.HTTP_400_BAD_REQUEST
                )

            if shipping_address:
                serializer = AddressSerializer(data=shipping_address)
                serializer.is_valid(raise_exception=True)
                order.address = serializer.save()
            else:
                order.address = customer.address
            order.save()

            match action:
                # Handle checkout action
                case "checkout":
                    return self._process_checkout(order, cart)

                # Handle save_order action
                case "save_order":
                    return self._process_save_order(order, cart)

                case _:
                    return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

    def _process_checkout(self, order, cart):
        """
        Handle the checkout process.
        """
        OrderItem.create_from_cart(order, cart)
        cart.clear()
        return redirect(reverse.reverse("payment", args=[order.id]))

    def _process_save_order(self, order, cart):
        """
        Handle saving the order without proceeding to payment.
        """
        OrderItem.create_from_cart(order, cart)
        cart.clear()
        return Response(
            {"success": "Your Order has been saved"},
            status=status.HTTP_201_CREATED,
        )


class OrderInstanceView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)

    @swagger_auto_schema(
        operation_summary="Get an order",
        responses={200: OrderItemSerializer(), 404: "Not Found"},
        tags=["Order"],
    )
    def get(self, request, pk):
        order = self.get_object()
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Update an order with a shipping address or voucher code",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "voucher_code": openapi.Schema(type=openapi.TYPE_STRING),
                "address": AddressSerializer,
            },
            example={
                "voucher_code": "SAVE10",
                "address": {
                    "street_address": "123 Main St",
                    "postal_code": "12345",
                    "city": "Anytown",
                    "state": "CA",
                    "country": "Canada",
                },
            },
        ),
        responses={201: OrderSerializer, 400: "Bad Request"},
        tags=["Order"],
    )
    def put(self, request, pk):
        order = self.get_object()

        # Only pending orders can be modified
        if order.status != Order.OrderStatus.AWAITING_PAYMENT:
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Apply discount if a discount code is provided
        if voucher_code := request.data.get("voucher_code"):
            voucher = Voucher.objects.get(code=voucher_code.upper())
            valid, msg = voucher.is_valid(order.customer, order.original_subtotal())
            
            if not valid:
                return Response({"voucher_code": msg}, status=status.HTTP_400_BAD_REQUEST)
            
            applied_offer = order.apply_offer(voucher)

            if not applied_offer:
                return Response(
                    {
                        "voucher_code": "Your order/order items are not eligible for this discount offer"
                    },
                    status=status.HTTP_201_CREATED,
                )

            voucher.update_usage_count()  # Update voucher usage count

        address = request.data.get("address")
        data = {"address": address}
        serializer = OrderSerializer(instance=order, data=data)
        serializer.context["request"] = request
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(operation_summary="Delete an order", tags=["Order"])
    def delete(self, request, pk):
        order = self.get_object()
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderItemView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderItemSerializer

    def get_queryset(self):
        customer_orders = Order.objects.filter(customer=self.request.user)
        queryset = OrderItem.objects.filter(order__in=customer_orders)
        return queryset

    def get_order_item(self, order_id, order_item_id):
        qs = self.get_queryset()
        return get_object_or_404(qs, id=order_item_id, order_id=order_id)

    def check_order_editable(self, customer, order_id):
        """
        Checks if an order's item can be modified based on its status.
        Only orders with a status of "awaiting_payment" can be edited.

        Args:
            customer (Customer): The customer to whom the order belongs to.
            order_id (UUID): The ID of the order to be modified

        Returns:
            HttpResponse 403: If the order can't if the order can't be modified.
            None: If the order is still awaiting payment.
        """
        order = get_object_or_404(Order.objects.filter(customer=customer), id=order_id)
        if order.status != Order.OrderStatus.AWAITING_PAYMENT:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return (
            True
            if order.status == Order.OrderStatus.AWAITING_PAYMENT
            else Response(status=status.HTTP_403_FORBIDDEN)
        )

    def dispatch(self, request, *args, **kwargs):
        order = self.get_object()
        if request.method.lower() != "get":
            return self.check_order_editable(request.user, order.id)
        return super().dispatch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Get an item from an order",
        responses={200: OrderItemSerializer(), 404: "Not Found"},
        tags=["Order"],
    )
    def get(self, request, order_id, item_id):
        order_item = self.get_order_item(order_id, item_id)
        serializer = self.get_serializer(order_item)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Update an item's quantity in a customer's order",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["quantity"],
            properties={
                "quantity": openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            example={"quantity": 12},
        ),
        responses={200: OrderItemSerializer, 400: "Bad Request", 404: "Not Found"},
        tags=["Order"],
    )
    def put(self, request, order_id, item_id):
        order_item = self.get_order_item(order_id, item_id)

        # Only the quantity of the item can be updated
        data = {"quantity": request.data.get("quantity", 1)}
        serializer = self.get_serializer(instance=order_item, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Delete an item from a user's order",
        tags=["Order"],
    )
    def delete(self, request, order_id, item_id):
        order_item = self.get_order_item(order_id, item_id)
        order_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
