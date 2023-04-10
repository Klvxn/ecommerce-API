from django.shortcuts import redirect
from django.urls import reverse
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view

from .models import Customer
from .permissions import CustomerOnly
from .serializers import CustomerSerializer, CustomerUpdateSerializer


# Create your views here.
class CustomerCreate(CreateAPIView):

    queryset = Customer.objects.all()
    permission_classes = [AllowAny]
    serializer_class = CustomerSerializer

    @swagger_auto_schema(operation_summary="Create a customer", tags=["customers"])
    def post(self, request, *args, **kwargs):
        return super().create(request, args, kwargs)


class CustomerInstance(RetrieveUpdateDestroyAPIView):

    queryset = Customer.objects.all()
    lookup_field = "pk"
    permission_classes = [CustomerOnly]
    serializer_class = CustomerSerializer

    def get_serializer_class(self):
        if self.request.method in ["PATCH", "PUT"]:
            return CustomerUpdateSerializer
        return super().get_serializer_class()

    @swagger_auto_schema(operation_summary="Get a customer by ID", tags=["customers"])
    def get(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
        return super().retrieve(request, args, kwargs)

    @swagger_auto_schema(operation_summary="Update a customer", tags=["customers"])
    def put(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
        return super().update(request, args, kwargs)

    @swagger_auto_schema(
        operation_summary="Partial update a customer", tags=["customers"]
    )
    def patch(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
        return super().update(request, args, kwargs)

    @swagger_auto_schema(operation_summary="Delete a customer", tags=["customers"])
    def delete(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
        return super().destroy(args, kwargs)


@swagger_auto_schema(
    "get", operation_summary="Get a customer's orders", tags=["customers"]
)
@api_view(["GET"])
def customer_orders(request, pk):
    return redirect(reverse("orders"))
