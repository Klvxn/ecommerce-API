from rest_framework import exceptions, status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema

from .models import Customer
from .permissions import CustomerOnly
from .serializers import CustomerSerializer, CustomerUpdateSerializer


# Create your views here.
class CustomerCreate(APIView):

    def get_permissions(self):
        if self.request.method == "POST":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get(self, request, *args, **kwargs):
        customers = Customer.objects.all()
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=CustomerSerializer)
    def post(self, request, *args, **kwargs):
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerInstance(APIView):

    permission_classes = [CustomerOnly]

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH"]:
            permission_classes = [CustomerOnly]
        else:
            permission_classes = [IsAdminUser | CustomerOnly]
        return [permission() for permission in permission_classes]

    def get_object(self, pk):
        try:
            return Customer.objects.get(pk=pk)
        except Customer.DoesNotExist:
            raise exceptions.NotFound({"error": "Customer with supplied ID doesn't exist."})

    def get(self, request, pk, *args, **kwargs):
        customer = self.get_object(pk=pk)
        serializer = CustomerSerializer(customer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=CustomerUpdateSerializer)
    def put(self, request, pk, *args, **kwargs):
        customer = self.get_object(pk=pk)
        serializer = CustomerUpdateSerializer(customer, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, *args, **kwargs):
        customer = self.get_object(pk=pk)
        customer.delete()
        return Response(
            {"message": "Customer has been deleted"}, status=status.HTTP_204_NO_CONTENT
        )
