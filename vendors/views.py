from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import Vendor
from .permissions import VendorOnly
from .serializers import VendorSerializer, VendorInstanceSerializer


# Create your views here.
class VendorViewSet(ModelViewSet):
    """
    API endpoint for managing vendor accounts.

    This viewset provides functionalities for listing, creating, retrieving, 
    updating, and deleting vendor accounts.
    """

    http_method_names = ["get", "post", "put", "delete"]
    lookup_field = "slug"
    queryset = Vendor.objects.all()
    permission_classes = [VendorOnly, IsAuthenticated]
    serializer_class = VendorSerializer

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [IsAuthenticated]

        elif self.action in ["update", "destroy"]:
            permission_classes = [VendorOnly]

        else:
            permission_classes = [AllowAny]

        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return VendorInstanceSerializer
        return super().get_serializer_class()

    @swagger_auto_schema(operation_summary="Get all vendors", tags=["vendors"])
    def list(self, request, *args, **kwargs):
        return super().list(request, args, kwargs)

    @swagger_auto_schema(operation_summary="Get a vendor", tags=["vendors"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, args, kwargs)

    @swagger_auto_schema(operation_summary="Create a vendor", tags=["vendors"])
    def create(self, request, *args, **kwargs):
        data = {
            "about": request.data["about"],
            "brand_name": request.data["brand_name"],
            "customer": request.user
        }
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(operation_summary="Update a vendor", tags=["vendors"])
    def update(self, request, *args, **kwargs):
        vendor = self.get_object()
        self.check_object_permissions(request, vendor)
        data = {
            "about": request.data.get("about"),
            "brand_name": request.data.get("brand_name")
        }
        serializer = self.get_serializer(vendor, data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(operation_summary="Delete a vendor", tags=["vendors"])
    def destroy(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
        return super().destroy(args, kwargs)
