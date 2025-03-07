from django.shortcuts import redirect
from django.urls import reverse
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
)
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Customer
from .permissions import CustomerOnly
from .serializers import CustomerSerializer, CustomerUpdateSerializer

# Create your views here.


@extend_schema_view(
    post=extend_schema(
        summary="Create a new customer",
        request=CustomerSerializer,
        responses={201: CustomerSerializer, 400: None, 401: None},
        tags=["customer"],
    ),
)
class CustomerCreateView(CreateAPIView):
    queryset = Customer.objects.all()
    permission_classes = [AllowAny]
    serializer_class = CustomerSerializer


@extend_schema_view(
    get=extend_schema(
        summary="Get a customer by ID",
        responses={200: CustomerSerializer, 401: None},
        tags=["customer"],
    ),
    put=extend_schema(
        summary="Update a customer",
        request=CustomerSerializer,
        responses={201: CustomerUpdateSerializer, 400: None, 401: None},
        tags=["customer"],
    ),
    delete=extend_schema(
        summary="Delete a customer",
        request=CustomerSerializer,
        responses={204: {}, 400: None, 401: None},
        tags=["customer"],
    ),
)
class CustomerInstanceView(RetrieveUpdateDestroyAPIView):
    http_method_names = ["get", "put", "delete"]
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

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(summary="Get a customer's orders", tags=["customer"])
@api_view(["GET"])
def customer_orders(request, pk):
    return redirect(reverse("orders"))
