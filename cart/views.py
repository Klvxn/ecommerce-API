from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiRequest,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from catalogue.models import Product, ProductVariant

from .cart import Cart
from .serializers import AddToCartSerializer


# Create your views here.
class CartView(GenericAPIView):
    """
    View for adding/viewing a customer's cart.
    """

    queryset = Product.objects.all()
    permission_classes = [AllowAny]
    http_method_names = ["get", "post", "delete"]
    serializer_class = AddToCartSerializer

    def get(self, request):
        cart = Cart(request)
        if cart.cart:
            return Response(
                {
                    "items": cart.cart,
                    "items count": len(cart),
                    "subtotal": cart.subtotal(),
                    "shipping": cart.total_shipping(),
                    "total": cart.total(),
                },
                status=status.HTTP_200_OK,
            )

        return Response({"info": "Your cart is empty"}, status=status.HTTP_200_OK)

    # def get_serializer_context(self):
    #     context = super().get_serializer_context()
    #     context["product_id"] = self.kwargs["pk"]
    #     return context

    @extend_schema(
        summary="Add a product to cart",
        request=OpenApiRequest("Add to cart", AddToCartSerializer()),
        examples=[
            OpenApiExample(
                "Valid Request",
                value={
                    "quantity": 12,
                    "variant_sku": "2f23232242f2f3f",
                },
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
        variant_sku = serializer.validated_data["variant_sku"]

        variant = get_object_or_404(ProductVariant, sku=variant_sku)

        cart = Cart(request)
        cart.add(variant, quantity)

        return Response(
            {
                "success": f"{quantity} of {variant} has been added to cart",
                "cart_total": cart.total(),
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request):
        cart = Cart(request)
        cart.clear()
        return Response({"success": "Cart has been cleared"}, status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    # GET method schema
    get=extend_schema(
        summary="Retrieve cart and its items",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "Items": {"type": "object"},
                    "Total items": {"type": "integer"},
                    "subtotal": {"type": "number"},
                    "Shipping": {"type": "number"},
                    "Total": {"type": "number"},
                },
                "info": {"type": "string"},
            }
        },
        tags=["cart"],
    ),
    # PUT method schema
    put=extend_schema(
        summary="Update an item in the cart",
        request={
            "type": "object",
            "required": ["product_sku", "quantity"],
            "properties": {"product_sku": {"type": "string"}, "quantity": {"type": "integer"}},
        },
        responses={
            200: {"type": "object", "properties": {"success": {"type": "string"}}},
            400: {"type": "object", "properties": {"error": {"type": "string"}}},
        },
        examples=[
            OpenApiExample("Example", value={"product_sku": "3_d845d16d", "quantity": 12})
        ],
        tags=["cart"],
    ),
    # DELETE method schema
    delete=extend_schema(
        summary="Remove an item from cart or clear the cart",
        request={"type": "object", "properties": {"product_sku": {"type": "string"}}},
        responses=[
            OpenApiResponse(
                response=204,
                description={"type": "object", "properties": {"success": {"type": "string"}}},
            )
        ],
        examples=[OpenApiExample("Example", value={"product_sku": "3_d845d16d"})],
        tags=["cart"],
    ),
)
class CartItemView(APIView):
    """
    View to handle cart-related operations:
    Updating and removing items from the cart.
    """

    permission_classes = [AllowAny]

    def put(self, request, item_key):
        cart = Cart(request)
        # item_key = str(request.data.get("item_key"))
        quantity = request.data.get("quantity")

        if not quantity:
            return Response(
                {"error": "Quantity is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if item_key in cart.cart.keys():
            cart.update(item_key, quantity=quantity)
            return Response({"success": "Cart updated"}, status=status.HTTP_200_OK)

        return Response(
            {"error": "This item is not in your cart"},
            status=status.HTTP_404_NOT_FOUND,
        )

    def delete(self, request, item_key):
        cart = Cart(request)
        # item_key = request.data.get("item_key")

        if item_key in cart.cart.keys():
            if removed := cart.remove(item_key):
                return Response(
                    {"success": "Item has been removed from cart"},
                    status=status.HTTP_204_NO_CONTENT,
                )

            return Response(
                {"error": "This item is not in your cart"},
                status=status.HTTP_404_NOT_FOUND,
            )
