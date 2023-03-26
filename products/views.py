from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import exceptions, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import LimitOffsetPagination
from cart.cart import Cart

from .models import Product
from .serializers import ProductInstanceSerializer, ProductsSerializer


# Create your views here.
class ProductsList(GenericAPIView, LimitOffsetPagination):

    permission_classes = [AllowAny]
    serializer_class = ProductsSerializer
    filterset_fields = ['category', 'available', 'vendor']
    search_fields = ['name', 'category__name', 'label', 'vendor__brand_name']

    def get_queryset(self):
        queryset = Product.objects.all()
        queryset = self.filter_queryset(queryset)
        return queryset

    @swagger_auto_schema(
        operation_summary="Get all available products",
        manual_parameters=[
            openapi.Parameter(
                name="search", in_=openapi.IN_QUERY, type=openapi.TYPE_STRING
            )
        ],
        responses={200: ProductsSerializer(many=True)},
        tags=["products"],
    )
    def get(self, request, slug=None):
        products = self.get_queryset()
        page = self.paginate_queryset(products)

        if slug:
            page = self.paginate_queryset(
                products.filter(category__slug=slug)
            )

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductInstance(GenericAPIView):

    queryset = Product.objects.all()
    permission_classes = [AllowAny]
    serializer_class = ProductInstanceSerializer

    def get_object(self):
        try:
            return super().get_object()
        except Product.DoesNotExist:
            raise exceptions.NotFound({"error": "Product not found."})

    @swagger_auto_schema(operation_summary="Retrieve a product", tags=["products"])
    def get(self, request, pk):
        product = self.get_object()
        serializer = self.get_serializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Add a product to cart",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            default=1,
            properties={
                "quantity": openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            example={"quantity": 12},
        ),
        tags=["products"],
    )
    def post(self, request, pk):
        product = self.get_object()
        user_cart = Cart(request)
        quantity = request.data.get("quantity")

        if quantity > product.stock:
            return Response(
                {"error": "The quantity cannot be more than product's stock"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_cart.add_item(product=product, quantity=quantity)
        return Response(
            {"success": f"{product} has been added to cart"},
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        operation_summary="Delete a product from cart", tags=["products"]
    )
    def delete(self, request, pk):
        product = self.get_object()
        user_cart = Cart(request)
        deleted = user_cart.remove_item(product)

        if deleted:
            return Response(
                {"message": f"{product} has been removed from cart."},
                status=status.HTTP_204_NO_CONTENT,
            )

        return Response(
            {"message": f"{product} is not in cart."},
            status=status.HTTP_400_BAD_REQUEST,
        )
