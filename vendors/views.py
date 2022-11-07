from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Vendor
from .serializers import VendorSerializer


# Create your views here.
class VendorCreate(CreateAPIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        brand_name = request.data["brand_name"]
        about = request.data["about"]
        customer = request.user
        vendor = Vendor.objects.create(about=about, brand_name=brand_name, customer=customer)
        serializer = VendorSerializer(vendor)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class VendorInstance(RetrieveAPIView):

    lookup_field = "slug"
    queryset = Vendor.objects.all()
    permission_classes = [AllowAny]
    serializer_class = VendorSerializer
