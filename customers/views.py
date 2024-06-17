from django.shortcuts import redirect
from django.urls import reverse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Customer
from .permissions import CustomerOnly
from .serializers import CustomerSerializer, CustomerUpdateSerializer


# Create your views here.
class CustomerCreateView(CreateAPIView):

    queryset = Customer.objects.all()
    permission_classes = [AllowAny]
    serializer_class = CustomerSerializer

    @swagger_auto_schema(operation_summary="Create a customer", tags=["Customer"])
    def post(self, request, *args, **kwargs):
        return super().create(request, args, kwargs)


class CustomerInstanceView(RetrieveUpdateDestroyAPIView):

    http_method_names = ["get", "post", "put", "delete"]
    queryset = Customer.objects.all()
    lookup_field = "pk"
    permission_classes = [CustomerOnly]
    serializer_class = CustomerSerializer

    def get_serializer_class(self):
        if self.request.method in ["PATCH", "PUT"]:
            return CustomerUpdateSerializer
        return super().get_serializer_class()

    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() != "get":
            self.check_object_permissions(request, self.get_object())
        return super().dispatch(request, args, kwargs)

    @swagger_auto_schema(operation_summary="Get a customer by ID", tags=["Customer"])
    def get(self, request, *args, **kwargs):
        return super().retrieve(request, args, kwargs)

    @swagger_auto_schema(operation_summary="Update a customer", tags=["Customer"])
    def put(self, request, *args, **kwargs):
        return super().update(request, args, kwargs)

    @swagger_auto_schema(operation_summary="Delete a customer", tags=["Customer"])
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(
    "get", operation_summary="Get a customer's orders", tags=["Customer"]
)
@api_view(["GET"])
def customer_orders(request, pk):
    return redirect(reverse("orders"))
