from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .cart import Cart


# Create your views here.
class CartView(APIView):
    """
    View to handle cart-related operations:
    
    Retrieving cart items, updating and removing items from the cart.
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(operation_summary="Retrieve items in the cart", tags=["cart"])
    def get(self, request, *args, **kwargs):
        user_cart = Cart(request)
        if user_cart.cart:

            return Response(
                {
                    "Items": user_cart.cart,
                    "Total items": len(user_cart),
                    "subtotal": user_cart.subtotal(),
                    "Shipping": user_cart.total_shipping_fee(),
                    "Total": user_cart.total_cost()
                },
                status=status.HTTP_200_OK,
            )

        return Response({"info": "Your cart is empty"}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Update an item in the cart",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["item_id", "quantity"],
            properties={
                "item_id": openapi.Schema(type=openapi.TYPE_STRING),
                "quantity": openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            example={
                "item_id": "3_d845d16d",
                "quantity": 12
            },
        ),
        tags=["cart"]
    )
    def put(self, request):
        user_cart = Cart(request)
        item_id = request.data.get("item_id")
        quantity = request.data.get("quantity")

        if not item_id or not quantity:
            return Response(
                {"error": "Both product_name and quantity are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if item_id in  user_cart.cart:
            user_cart.update_item(item_id, quantity=quantity)
            return Response(
                {"success": "Cart updated"}, status=status.HTTP_200_OK
            )

        return Response(
            {"error": f"This item: {item_id} is not in your cart"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @swagger_auto_schema(
        operation_summary="Remove an item from cart or clear the cart",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "item_id": openapi.Schema(type=openapi.TYPE_STRING),
            },
            example={"item_id": "3_d845d16d"},
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

        for item_id in request.data:
            removed = user_cart.remove_item(item_id)
            if removed:
                return Response(
                    {"success": "Item has been removed from cart"},
                    status=status.HTTP_204_NO_CONTENT,
                )

            return Response(
                {"error": "This item is not in your cart"},
                status=status.HTTP_400_BAD_REQUEST,
            )
