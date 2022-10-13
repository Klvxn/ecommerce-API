from django.db.models import Q

from drf_yasg.utils import swagger_auto_schema
from rest_framework import exceptions, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.views import APIView
from rest_framework.response import Response

from cart.cart import Cart

from .models import Product
from .serializers import ProductSerializer


# Create your views here.
class ProductsList(APIView):

    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get(self, request, slug=None, *args, **kwargs):
        available_products = Product.objects.filter(available=True)
        if request.query_params:
            query = request.query_params.get("search")
            products = available_products.filter(
                Q(name__icontains=query) | Q(category__name__icontains=query)
            )
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif slug:
            products = available_products.filter(category__slug=slug)
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = ProductSerializer(available_products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductInstance(APIView):

    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        try:
            return Product.objects.get(available=True, pk=pk)
        except Product.DoesNotExist:
            raise exceptions.NotFound({"error": "Product doesn't exist."})

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH"]:
            permission_classes = [IsAdminUser]
            return [permission() for permission in permission_classes]
        return super().get_permissions()

    def get(self, request, pk, *args, **kwargs):
        product = self.get_object(pk=pk)
        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_description="Add a product to cart")
    def post(self, request, pk, *args, **kwargs):
        product = self.get_object(pk=pk)
        user_cart = Cart(request)
        quantity = request.data.get("quantity", 1)
        user_cart.add_item(product=product, quantity=quantity)
        return Response(
            {"success": f"{product} has been added to cart"},
            status=status.HTTP_201_CREATED,
        )

    def put(self, request, pk, *args, **kwargs):
        product = self.get_object(pk=pk)
        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
            {"message": f"{product} is not in cart."}, status=status.HTTP_409_CONFLICT
        )
