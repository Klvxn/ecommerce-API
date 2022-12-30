from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, IsAdminUser

from .models import Customer
from .permissions import CustomerOnly
from .serializers import CustomerSerializer, CustomerUpdateSerializer


# Create your views here.
class CustomerCreate(ListCreateAPIView):

    queryset = Customer.objects.all()
    permission_classes = [IsAdminUser]
    serializer_class = CustomerSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            permission_classes = [AllowAny]
            return [permission() for permission in permission_classes]
        return super().get_permissions()


class CustomerInstance(RetrieveUpdateDestroyAPIView):

    queryset = Customer.objects.all()
    lookup_field = "pk"
    permission_classes = [CustomerOnly]
    serializer_class = CustomerSerializer

    def get_serializer_class(self):
        if self.request.method in ["PATCH", "PUT"]:
            return CustomerUpdateSerializer
        return super().get_serializer_class()
