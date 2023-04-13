from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import exceptions, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView

from customers.serializers import AddressSerializer

from .models import Order
from .serializers import OrderSerializer


# Create your views here.
class OrdersListView(GenericAPIView, LimitOffsetPagination):

    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    filterset_fields = ['status']

    def get_queryset(self):
        queryset = Order.objects.filter(customer=self.request.user)
        queryset = self.filter_queryset(queryset)
        return queryset

    @swagger_auto_schema(
        operation_summary="Get all orders by a customer",
        manual_parameters=[
            openapi.Parameter("status", in_=openapi.IN_QUERY, type=openapi.TYPE_STRING)
        ],
        tags=["orders"],
    )
    def get(self, request):
        orders = self.get_queryset()
        page = self.paginate_queryset(orders)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderInstanceView(GenericAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)

    def get_object(self, pk):
        order = self.get_queryset().filter(pk=pk).first()

        if order is None:
            raise exceptions.NotFound(
                {"error": "Order with supplied Order ID not found"}
            )

        return order

    @swagger_auto_schema(
        operation_summary="Get an order by ID",
        tags=["orders"],
    )
    def get(self, request, pk):
        order = self.get_object(pk)
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Update an order with an address.",
        request_body=AddressSerializer,
        responses={201: OrderSerializer, 400: "Bad Request"},
        tags=["orders"],
    )
    def put(self, request, pk):
        order = self.get_object(pk)
        data = {"address": request.data}
        serializer = OrderSerializer(instance=order, data=data)
        serializer.context["request"] = request
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary="Delete an order by ID.",
        tags=["orders"],
    )
    def delete(self, request, pk):
        order = self.get_object(pk)
        order.delete()
        return Response(
            {"message": "Order has been deleted"}, status=status.HTTP_204_NO_CONTENT
        )
