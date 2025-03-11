from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiRequest,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from catalogue.models import Product

from .cart import Cart
from .serializers import AddCartItemSerializer, UpdateCartItemSerializer


# Create your views here.
class CartView(GenericAPIView):
    """
    View for viewing and adding items to cart.
    """

    queryset = Product.objects.all()
    permission_classes = [AllowAny]
    http_method_names = ["get", "post", "delete"]
    serializer_class = AddCartItemSerializer

    def get(self, request):
        cart = Cart(request)
        if cart.cart_items:
            return Response(
                {
                    "items": cart.cart_items.values(),
                    "count": len(cart),
                    "subtotal": cart.subtotal(),
                    "shipping": cart.total_shipping(),
                    "total": cart.total(),
                },
                status=status.HTTP_200_OK,
            )
        return Response({"message": "Your cart is empty"}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Add a product to cart",
        request=OpenApiRequest("Add to cart", AddCartItemSerializer()),
        examples=[
            OpenApiExample(
                "Valid Request",
                value={"quantity": 12, "variant_sku": "2f23232242f2f3f"},
                request_only=True,
                response_only=False,
            )
        ],
        responses=[
            OpenApiResponse(
                response=200,
                description="Successfuly added to cart",
                examples=[OpenApiExample("Example", value={"message": "Successfuly"})],
            )
        ],
        tags=["Cart"],
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity = serializer.validated_data["quantity"]
        variant = serializer.validated_data["variant"]

        cart = Cart(request)
        cart.add(variant, quantity)
        return Response(
            {
                "success": f"{quantity}x {variant} has been added",
                "cart_total": cart.total(),
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request):
        cart = Cart(request)
        cart.clear()
        return Response({"success": "Cart has been cleared"}, status=status.HTTP_204_NO_CONTENT)


class CartItemView(GenericAPIView):
    """
    View to managing cart items.
    """
    serializer_class = UpdateCartItemSerializer
    permission_classes = [AllowAny]

    def put(self, request):
        cart = Cart(request)
        serializer = UpdateCartItemSerializer(data=request.data, context={"cart": cart})
        if serializer.is_valid(raise_exception=True):

            item_key = serializer.validated_data["item_key"]
            quantity = serializer.validated_data["quantity"]
            updated, msg = cart.update(item_key, quantity=quantity)
            return Response({"success": updated, "message": msg}, status=status.HTTP_200_OK) 

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        cart = Cart(request)
        serializer = UpdateCartItemSerializer(data=request.data, context={"cart": cart})
        if serializer.is_valid(raise_exception=True):

            item_key = serializer.validated_data["item_key"]
            if item_key in cart.cart_items.keys() and cart.remove(item_key):
                return Response(
                    {"success": True, "message": "Item has been removed from cart"},
                    status=status.HTTP_204_NO_CONTENT,
                )

            return Response(
                {"success": False, "message": "This item is not in your cart"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartVoucherView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Apply voucher code to a customer's cart
        """
        voucher_code = request.data.get("voucher_code")
        if not voucher_code:
            return Response(
                {"voucher_code": "Voucher code is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        cart = Cart(request)
        applied, msg = cart.apply_voucher(voucher_code=voucher_code)

        if not applied:
            return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"success": msg}, status=status.HTTP_200_OK)

    def delete(self, request):
        """
        Remove applied voucher from a customer's cart
        """
        cart = Cart(request)
        removed = cart.remove_voucher()
        if not removed:
            return Response({"error": "No applied voucher to remove"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"success": "Applied voucher has been successfully removed"},
            status=status.HTTP_200_OK,
        )
