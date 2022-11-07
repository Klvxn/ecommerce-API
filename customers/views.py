from drf_yasg.utils import swagger_auto_schema
from rest_framework import exceptions, status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Customer
from .permissions import CustomerOnly
from .serializers import CustomerSerializer, CustomerUpdateSerializer


# Create your views here.
class CustomerCreate(APIView):

    permission_classes = [IsAdminUser]

    def get_permissions(self):
        if self.request.method == "POST":
            permission_classes = [AllowAny]
            return [permission() for permission in permission_classes]
        return super().get_permissions()

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

    def get_object(self, pk):
        try:
            return Customer.objects.get(pk=pk)
        except Customer.DoesNotExist:
            raise exceptions.NotFound(
                {"error": "Customer with supplied ID doesn't exist."}
            )

    def get(self, request, pk, *args, **kwargs):
        self.check_permissions(request)
        customer = self.get_object(pk=pk)
        self.check_object_permissions(request, obj=customer)
        serializer = CustomerSerializer(customer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=CustomerUpdateSerializer)
    def put(self, request, pk, *args, **kwargs):
        customer = self.get_object(pk=pk)
        self.check_object_permissions(request, obj=customer)
        serializer = CustomerUpdateSerializer(customer, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, *args, **kwargs):
        customer = self.get_object(pk=pk)
        self.check_object_permissions(request, obj=customer)
        customer.delete()
        return Response(
            {"message": "Customer has been deleted"}, status=status.HTTP_204_NO_CONTENT
        )
