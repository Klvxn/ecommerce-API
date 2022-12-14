from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order, OrderItem
from orders.serializers import OrderSerializer
from products.models import Product

from .cart import Cart


# Create your views here.
class CartView(APIView):

    permission_classes = [AllowAny]

    @swagger_auto_schema(operation_summary="Retrieves items in the cart")
    def get(self, request, *args, **kwargs):
        user_cart = Cart(request)
        if user_cart.cart:
            data = []
            for item in user_cart:
                data.append(item)
            return Response(
                {
                    "Cart items": data,
                    "Items count": len(user_cart),
                    "Total cost": user_cart.get_total_cost(),
                },
                status=status.HTTP_200_OK,
            )
        return Response({"message": "Your cart is empty"}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Creates an order from user's cart if 'save_for_later' is true",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["save_for_later"],
            properties={
                "save_for_later": openapi.Schema(type=openapi.TYPE_BOOLEAN),
            },
            example={"save_for_later": "true"},
        ),
        responses={201: OrderSerializer, 400: "Bad request"},
    )
    @method_decorator(login_required(login_url="/api/v1/api-auth/login/"))
    def post(self, request, *args, **kwargs):
        data = request.data
        action = data.get("save_for_later", False)
        user_cart = Cart(request)
        if action:
            if len(user_cart) > 0:
                order = Order.objects.create(customer=request.user)
                for item in user_cart:
                    product = Product.objects.get(name=item["product"])
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item.get("quantity", 1),
                        cost_per_item=item.get("price", product.price),
                    )
                user_cart.clear()
                return Response(
                    {
                        "success": f"Your Order has been saved and your Order ID is {order.id}."
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    {"error": "Can't create an order. Your cart is empty"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(
            {"save_for_later": ["This field is required"]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @swagger_auto_schema(
        operation_summary="Updates an item in the cart",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["product_name", "quantity"],
            properties={
                "product_name": openapi.Schema(type=openapi.TYPE_STRING),
                "quantity": openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            example={"product_name": "new quantity"},
        ),
    )
    def put(self, request, *args, **kwargs):
        """
        Updates an item in the cart with a new quantity if the product exists in the cart
        """
        data = request.data
        user_cart = Cart(request)
        for key, value in data.items():
            product = get_object_or_404(Product, name=key)
            if str(product.id) in user_cart.cart.keys():
                user_cart.update_item(product, quantity=value)
                return Response(
                    {"message": "Cart updated"}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"message": "This item is not in your cart"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    @swagger_auto_schema(
        operation_summary="Removes an item from cart or clears the cart",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "product_name": openapi.Schema(type=openapi.TYPE_STRING),
            },
            example={"product_name": ""},
        ),
    )
    def delete(self, request, *args, **kwargs):
        """
        Removes an item from the cart if item is specified in request body, else the cart will be cleared
        """
        data = request.data
        user_cart = Cart(request)
        if data:
            for key in data.keys():
                product = get_object_or_404(Product, name=key)
                removed = user_cart.remove_item(product)
                if removed:
                    return Response(
                        {"message": "Item has been removed from cart"},
                        status=status.HTTP_204_NO_CONTENT,
                    )
                else:
                    return Response(
                        {"message": "This item is not in your cart"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
        user_cart.clear()
        return Response(
            {"message": "Cart has been cleared"}, status=status.HTTP_204_NO_CONTENT
        )
