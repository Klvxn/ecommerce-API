from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from catalogue.models import Product

from .cart import Cart


# Create your views here.
class CartView(APIView):
    """
    View to handle cart-related operations:
    
    retrieving cart items, creating orders from the cart, updating and
    removing items from the cart.
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(operation_summary="Retrieve items in the cart", tags=["cart"])
    def get(self, request, *args, **kwargs):
        user_cart = Cart(request)
        if user_cart.cart:
            data = [item for item in user_cart]

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
        operation_summary="Update an item in the cart",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["product_name", "quantity"],
            properties={
                "product_name": openapi.Schema(type=openapi.TYPE_STRING),
                "quantity": openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            example={
                "product_name": "Logitech Wireless Mouse",
                "quantity": 12
            },
        ),
        tags=["cart"]
    )
    def put(self, request):
        user_cart = Cart(request)
        product_name = request.data.get("product_name")
        quantity = request.data.get("quantity")

        if not product_name or not quantity:
            return Response(
                {"error": "Both product_name and quantity are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product = get_object_or_404(Product, name=product_name)
                    
        if str(product.id) in user_cart.cart.keys():
            user_cart.update_item(product, quantity=quantity)
            return Response(
                {"success": "Cart updated"}, status=status.HTTP_200_OK
            )

        return Response(
            {"error": f"This item: {product_name} is not in your cart"},
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

        for product_name in request.data.keys():
            product = get_object_or_404(Product, name=product_name)
            removed = user_cart.remove_item(product)

            if removed:
                return Response(
                    {"success": "Item has been removed from cart"},
                    status=status.HTTP_204_NO_CONTENT,
                )

            return Response(
                {"error": "This item is not in your cart"},
                status=status.HTTP_400_BAD_REQUEST,
            )
