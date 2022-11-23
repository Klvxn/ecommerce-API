from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import Vendor
from .permissions import VendorOnly
from .serializers import VendorSerializer


# Create your views here.
class VendorViewSet(ModelViewSet):

    lookup_field = "slug"
    queryset = Vendor.objects.all()
    permission_classes = [VendorOnly, IsAuthenticated]
    serializer_class = VendorSerializer

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update", "destroy"]:
            permission_classes = [VendorOnly]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

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

    def update(self, request, *args, **kwargs):
        vendor = self.get_object()
        self.check_object_permissions(request, vendor)
        data = {
            "about": request.data.get("about", vendor.about),
            "brand_name": request.data.get("brand_name", vendor.brand_name)
        }
        serializer = self.get_serializer(vendor, data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        self.check_object_permissions(request, self.get_object())
        return super().destroy(args, kwargs)
