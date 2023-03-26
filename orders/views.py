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
class OrdersList(GenericAPIView, LimitOffsetPagination):

    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self, request):
        return Order.objects.filter(customer=request.user)

    @swagger_auto_schema(
        operation_summary="Get all orders by a customer",
        manual_parameters=[
            openapi.Parameter("status", in_=openapi.IN_QUERY, type=openapi.TYPE_STRING)
        ],
        tags=["orders"],
    )
    def get(self, request):
        orders = self.get_queryset(request)
        page = self.paginate_queryset(orders)
        query = request.query_params.get("status")

        if query is not None:
            page = self.paginate_queryset(orders.filter(status=query))

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderInstance(GenericAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self, request):
        return Order.objects.filter(customer=request.user)

    def get_object(self, request, pk):
        order = self.get_queryset(request).filter(pk=pk).first()

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
        order = self.get_object(request, pk)
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Update an order with a new address.",
        request_body=AddressSerializer,
        responses={201: OrderSerializer, 400: "Bad Request"},
        tags=["orders"],
    )
    def put(self, request, pk):
        order = self.get_object(request, pk)
        data = {"address": request.data}
        serializer = self.get_serializer(order, data=data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Delete an order by ID.",
        tags=["orders"],
    )
    def delete(self, request, pk):
        order = self.get_object(request, pk)
        order.delete()
        return Response(
            {"message": "Order has been deleted"}, status=status.HTTP_204_NO_CONTENT
        )
