from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView

from catalogue.models import Product

from .models import Wishlist
from .serializers import WishlistSerializer


# Create your views here.
class WishlistListView(GenericAPIView):
    """
    API endpoint for managing a customer's wishlist.
    """

    http_method_names = ["get", "post"]
    permission_classes = [IsAuthenticated]
    serializer_class = WishlistSerializer
    search_fields = ["name", "item__product__name"]

    def get_queryset(self):
        queryset = Wishlist.objects.filter(owner=self.request.user)
        queryset = self.filter_queryset(queryset)
        return queryset

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        context = self.get_serializer_context()
        context["owner"] = request.user
        serializer = self.get_serializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WishlistInstanceView(GenericAPIView):
    queryset = Wishlist.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = WishlistSerializer
    search_fields = ["item__product__name"]

    def get_queryset(self):
        queryset = Wishlist.objects.filter(owner=self.request.user)
        queryset = self.filter_queryset(queryset)
        return queryset

    def dispatch(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_private:
            self.check_object_permissions(request, instance)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, pk):
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"error": "Product is required"}, status=status.HTTP_400_BAD_REQUEST)
        product = get_object_or_404(Product, pk=product_id)
        self.get_object().add(product)
        return Response(status=status.HTTP_201_CREATED)

    def put(self, request, pk):
        serializer = self.get_serializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        product_id = request.data.get("product_id")
        if not product_id:
            self.get_object().delete()
        else:
            product = get_object_or_404(Product, pk=product_id)
            self.get_object().remove(product)
        return Response(status=status.HTTP_204_NO_CONTENT)
