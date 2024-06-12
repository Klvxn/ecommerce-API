from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from customers.serializers import AddressSerializer
from orders.models import Order, OrderItem
from orders.serializers import OrderSerializer
from products.models import Discount, Product

from .cart import Cart


# Create your views here.
class CartView(APIView):

    permission_classes = [AllowAny]

    @swagger_auto_schema(operation_summary="Retrieve items in the cart", tags=["cart"])
    def get(self, request, *args, **kwargs):
        user_cart = Cart(request)
        if user_cart.cart:
            data = []
            for item in user_cart:
                data.append(item)

            return Response(
                {
                    "Cart items": data,
                    "Total items": len(user_cart),
                    "Shipping": f"${user_cart.get_total_shipping_fee()}",
                    "Total cost": f"${user_cart.get_total_cost()}",
                },
                status=status.HTTP_200_OK,
            )

        return Response({"info": "Your cart is empty"}, status=status.HTTP_200_OK)

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
                "action": "create_order",
                "discount_code": "SAVE10",
                "address": {
                    "street": "123 Main St",
                    "postal_code": "12345",
                    "city": "Anytown",
                    "state": "CA",
                    "country": "Canada",
                }
            },
        ),
        responses={201: OrderSerializer, 400: "Bad request"},
        tags=["cart"]
    )
    @method_decorator(login_required(login_url="/auth/login/"))
    def post(self, request):
        """
        Handle POST request to create an order from the user's cart.

        Args:
            request (Request): The HTTP request containing user and cart data.

        Returns:
            Response: HTTP response with order details or error messages.
        """
        action = request.data.get("action")
        discount_code = request.data.get("discount_code")
        shipping_address = request.data.get("address")
        user_cart = Cart(request)
        
        if action not in ("create_order", "save_order"):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if action and len(user_cart) <= 0:
            return Response(
                {"error": "Can't create an order. Your cart is empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        customer = request.user
        order = Order.objects.create(customer=customer)
        
        if discount_code:
            discount = Discount.order_discounts.filter(code=discount_code).first()
            if discount and discount.is_valid():
                
                if discount.minimum_order_value < user_cart.get_total_cost():
                    order.discount = discount
                    order.save()
                
                else:
                    return Response({
                        "error": f"The order total must be at least ${discount.minimum_order_value} to use this discount code"
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(
                    {"error": "Invalid discount code or discount has expired"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if action == "create_order":
            address = shipping_address or customer.address
            if address is None:
                return Response(
                    {"error": "Shipping address was not provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = AddressSerializer(data=address)
            if serializer.is_valid(raise_exception=True):
                order.address = serializer.save()
                order.save()

            OrderItem.create_from_cart(order, user_cart)
            user_cart.clear()
            context = {"request": request}
            serializer = OrderSerializer(order, context=context)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif action == "save_order":
            OrderItem.create_from_cart(order, user_cart)
            user_cart.clear()
            return Response(
                {
                    "success": f"Your Order has been saved and your Order ID is {order.id}."
                },
                status=status.HTTP_201_CREATED,
            )

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Update an item in the cart",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["product_name", "quantity"],
            properties={
                "product_name": openapi.Schema(type=openapi.TYPE_STRING),
                "quantity": openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            example={"product_name": 32},
        ),
        tags=["cart"]
    )
    def put(self, request):
        user_cart = Cart(request)

        for key, value in request.data.items():
            product = get_object_or_404(Product, name=key)
            
            if str(product.id) in user_cart.cart.keys():
                user_cart.update_item(product, quantity=value)
                return Response(
                    {"success": "Cart updated"}, status=status.HTTP_200_OK
                )

            else:
                return Response(
                    {"error": "This item is not in your cart"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    @swagger_auto_schema(
        operation_summary="Remove an item from cart or clear the cart",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "product_name": openapi.Schema(type=openapi.TYPE_STRING),
            },
            example={"product_name": "Wireless Keyboard"},
        ),
        tags=["cart"]
    )
    def delete(self, request):
        user_cart = Cart(request)
        if not request.data:
            user_cart.clear()
            return Response(
                {"success": "Cart has been cleared"}, status=status.HTTP_204_NO_CONTENT
            )

        for key in request.data.keys():
            product = get_object_or_404(Product, name=key)
            removed = user_cart.remove_item(product)

            if removed:
                return Response(
                    {"success": "Item has been removed from cart"},
                    status=status.HTTP_204_NO_CONTENT,
                )

            else:
                return Response(
                    {"error": "This item is not in your cart"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
