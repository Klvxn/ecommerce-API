from django.db import transaction
from django.shortcuts import redirect
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, reverse
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView, get_object_or_404

from customers.serializers import AddressSerializer
from cart.cart import Cart
from .models import Order, OrderItem
from .serializers import OrderItemSerializer, OrderSerializer


# Create your views here.
class OrdersListView(GenericAPIView, LimitOffsetPagination):

    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    filterset_fields = ['status']

    def get_queryset(self):
        queryset = Order.objects.filter(customer=self.request.user)
        queryset = self.filter_queryset(queryset)
        return queryset

    @swagger_auto_schema(
        operation_summary="Get all orders by a customer",
        manual_parameters=[
            openapi.Parameter("status", in_=openapi.IN_QUERY, type=openapi.TYPE_STRING)
        ],
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
                "discount_code": openapi.Schema(type=openapi.TYPE_STRING),
                "address": openapi.Schema(type=openapi.TYPE_OBJECT)
            },
            example={
                "action": "checkout",
                "discount_code": "SAVE10",
                "address": {
                    "street_address": "123 Main St",
                    "postal_code": "12345",
                    "city": "Anytown",
                    "state": "CA",
                    "country": "Canada",
                }
            },
        ),
        responses={201: OrderSerializer, 400: "Bad request"},
        tags=["Order"]
    )
    def post(self, request):
        """
        Handle POST request to create an order from the user's cart.

        Args:
            request (Request): The HTTP request containing user and cart data.

        Returns:
            Response: HTTP response with order details or error messages.
        """
        action = request.data.get("action")
        discount_code = request.data.get("discount_code", "", ).upper()
        shipping_address = request.data.get("address")
        user_cart = Cart(request)

        if action not in ("checkout", "save_order"):
            return Response(
                {"error": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST
            )

        if len(user_cart) <= 0:
            return Response(
                {"error": "Can't create an order. Your cart is empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        customer = request.user
        with transaction.atomic():
            order = Order.objects.create(customer=customer)

            if discount_code:
                pass

            address = shipping_address or customer.address
            if not address:
                return Response(
                    {"error": "Shipping address was not provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            match action:
                case "checkout":
                    if shipping_address:
                        serializer = AddressSerializer(data=shipping_address)
                        serializer.is_valid(raise_exception=True)
                        order.address = serializer.save()
                        order.save()
                    else:
                        order.address = customer.address
                        order.save()

                    OrderItem.create_from_cart(order, user_cart)
                    user_cart.clear()
                    # Redirect customer to the checkout page for payment
                    return redirect(reverse.reverse("payment", order.id))

                case "save_order":
                    OrderItem.create_from_cart(order, user_cart)
                    user_cart.clear()
                    return Response(
                        {"success": f"Your Order has been saved"},
                        status=status.HTTP_201_CREATED,
                    )


class OrderInstanceView(GenericAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)

    def get_object(self, id):
        return get_object_or_404(self.get_queryset(), id=id)

    @swagger_auto_schema(
        operation_summary="Get an order by ID",
        responses={200: OrderItemSerializer(), 404: "Not Found"},
        tags=["Order"]
    )
    def get(self, request, pk):
        order = self.get_object(pk)
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Update an order with a shipping address.",
        request_body=AddressSerializer,
        responses={201: OrderSerializer, 400: "Bad Request"},
        tags=["Order"],
    )
    def put(self, request, pk):
        order = self.get_object(pk)
        data = {"address": request.data}
        serializer = OrderSerializer(instance=order, data=data)
        serializer.context["request"] = request
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(operation_summary="Delete an order by ID.", tags=["Order"])
    def delete(self, request, pk):
        order = self.get_object(pk)
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
        return  get_object_or_404(qs, id=order_item_id, order_id=order_id)

    @swagger_auto_schema(
        operation_summary="Get an item from an order",
        responses={200: OrderItemSerializer(), 404: "Not Found"},
        tags=["Order"]
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
        responses={
            200: OrderItemSerializer, 400: "Bad Request", 404: "Not Found"
        },
        tags=["Order"],
    )
    def put(self, request, order_id, item_id):
        order_item = self.get_order_item(order_id, item_id)
        # Only the quantity of the item can be updated
        data = {"quantity": request.data.get("quantity")}
        serializer = self.get_serializer(instance=order_item, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Delete an item from a user's order", tags=["Order"],
    )
    def delete(self, request, order_id, item_id):
        order_item = self.get_order_item(order_id, item_id)
        order_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)