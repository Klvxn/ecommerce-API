from django.db.models import Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import exceptions, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.cart import Cart

from .models import Product
from .serializers import ProductInstanceSerializer, ProductsSerializer


# Create your views here.
class ProductsList(APIView):

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name="search", in_=openapi.IN_QUERY, type=openapi.TYPE_STRING
            )
        ],
        responses={200: ProductsSerializer(many=True)},
    )
    def get(self, request, slug=None, *args, **kwargs):
        available_products = Product.objects.filter(available=True)
        context = {"request": request}
        if request.query_params:
            query = request.query_params.get("search")
            products = available_products.filter(
                Q(name__icontains=query) | Q(category__name__icontains=query)
            )
            serializer = ProductsSerializer(products, context=context, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif slug:
            products = available_products.filter(category__slug=slug)
            serializer = ProductsSerializer(products, context=context, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = ProductsSerializer(available_products, context=context, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductInstance(APIView):

    permission_classes = [AllowAny]

    def get_object(self, pk):
        try:
            return Product.objects.get(available=True, pk=pk)
        except Product.DoesNotExist:
            raise exceptions.NotFound({"error": "Product not found."})

    def get(self, request, pk, *args, **kwargs):
        context = {"request": request}
        product = self.get_object(pk=pk)
        serializer = ProductInstanceSerializer(product, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Adds a product to cart",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            default=1,
            properties={
                "quantity": openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            example={"quantity": 12},
        ),
    )
    def post(self, request, pk, *args, **kwargs):
        product = self.get_object(pk=pk)
        user_cart = Cart(request)
        quantity = request.data.get("quantity", 1)
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

    @swagger_auto_schema(operation_summary="Deletes a product from cart")
    def delete(self, request, pk, *args, **kwargs):
        product = self.get_object(pk=pk)
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
