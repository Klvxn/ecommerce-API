from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiRequest,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
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
@extend_schema_view(
    get=extend_schema(
        summary="Retrieve customer's  cart and cart items",
        responses={
            200: OpenApiResponse(response=OpenApiTypes.OBJECT),
        },
        tags=["Cart"],
    ),
    post=extend_schema(
        summary="Add a product to cart",
        request=OpenApiRequest(
            AddCartItemSerializer,
            examples=[
                OpenApiExample(
                    "Valid Request", value={"quantity": 2, "variant_sku": "SKWIUBIBWI124"}
                )
            ],
        ),
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Successful",
                examples=[
                    OpenApiExample(
                        "Success response",
                        value={
                            "success": True,
                            "message": "2x Campari Wine 75cl has been added",
                            "cart_total": 23.5,
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request",
                examples=[
                    OpenApiExample(
                        "Invalid quantity",
                        value={
                            "success": False,
                            "message": "Requested quantity: 8 exceeds available stock: 3 for this variant",
                            "cart_total": 0.00,
                        },
                    )
                ],
            ),
        },
        tags=["Cart"],
    ),
    delete=extend_schema(
        summary="Delete customer's cart",
        responses={204: OpenApiResponse(response=OpenApiTypes.OBJECT)},
        tags=["Cart"],
    ),
)
class CartView(GenericAPIView):
    """
    View for viewing and adding items to cart.
    """

    queryset = Product.active_objects.all()
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
                    "savings": cart.get_total_discounts(),
                    "shipping": cart.total_shipping(),
                    "total": cart.total(),
                },
                status=status.HTTP_200_OK,
            )
        return Response({"message": "Your cart is empty"}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity = serializer.validated_data["quantity"]
        variant = serializer.validated_data["variant"]

        cart = Cart(request)
        cart.add(variant, quantity)
        return Response(
            {
                "success": True,
                "message": f"{quantity}x {variant} has been added",
                "cart_total": cart.total(),
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request):
        cart = Cart(request)
        cart.clear()
        return Response(
            {"success": True, "message": "Cart has been cleared"},
            status=status.HTTP_204_NO_CONTENT,
        )


@extend_schema_view(
    put=extend_schema(
        request=UpdateCartItemSerializer,
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Successful",
                examples=[
                    OpenApiExample(
                        "Success response",
                        value={"success": True, "message": "Cart item has been updated"},
                    )
                ],
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request",
                examples=[
                    OpenApiExample(
                        "Unavailable item",
                        value={
                            "success": False,
                            "message": "Item is no longer available and was removed",
                        },
                    )
                ],
            ),
        },
        tags=["Cart"],
    ),
    delete=extend_schema(
        responses={
            204: OpenApiResponse(
                response=OpenApiTypes.NONE, description="Successful, No content"
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Not found",
                examples=[
                    OpenApiExample(
                        "Item not found",
                        value={"success": False, "message": "This item is not in your cart"},
                    )
                ],
            ),
        },
        tags=["Cart"],
    ),
)
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


@extend_schema_view(
    post=extend_schema(
        request=OpenApiRequest(
            request=OpenApiTypes.OBJECT,
            examples=[OpenApiExample("Valid Request", value={"voucher_code": "SUMMER2021"})],
        ),
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Created",
                examples=[
                    OpenApiExample(
                        "Success response",
                        value={"success": True, "message": "Voucher has been applied"},
                    )
                ],
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request",
                examples=[
                    OpenApiExample(
                        "Invalid voucher code",
                        value={
                            "success": False,
                            "message": "No item in your cart is eligible for this voucher offer",
                        },
                    )
                ],
            ),
        },
        tags=["Cart"],
    ),
    delete=extend_schema(
        responses={
            204: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Successful",
                examples=[
                    OpenApiExample(
                        "Success response",
                        value={
                            "success": True,
                            "message": "Applied voucher has been successfully removed",
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request",
                examples=[
                    OpenApiExample(
                        "No applied voucher",
                        value={"success": False, "message": "No applied voucher to remove"},
                    )
                ],
            ),
        },
        tags=["Cart"],
    ),
)
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
            return Response(
                {"success": False, "message": msg}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response({"success": True, "message": msg}, status=status.HTTP_200_OK)

    def delete(self, request):
        """
        Remove applied voucher from a customer's cart
        """
        cart = Cart(request)
        removed = cart.remove_voucher()
        if not removed:
            return Response(
                {"success": False, "message": "No applied voucher to remove"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"success": True, "message": "Applied voucher has been successfully removed"},
            status=status.HTTP_204_NO_CONTENT,
        )
