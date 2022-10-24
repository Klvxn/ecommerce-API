from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from rest_framework import exceptions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.cart import Cart
from customers.models import Address
from customers.serializers import AddressSerializer
from products.models import Product

from .models import Order, OrderItem
from .serializers import OrderSerializer


# Create your views here.
class OrdersList(APIView):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[openapi.Parameter(
            "status",
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_STRING
        )]
    )
    def get(self, request, *args, **kwargs):
        customer = request.user
        context = {"request": request}
        if request.query_params:
            query = request.query_params.get("status")
            orders = Order.objects.filter(customer=customer, status=query)
            serializer = OrderSerializer(orders, context=context, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        orders = Order.objects.filter(customer=customer)
        serializer = OrderSerializer(orders, context=context, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Creates an order from cart items.",
        request_body=AddressSerializer,
        responses={201: OrderSerializer},
    )
    def post(self, request, *args, **kwargs):
        user_cart = Cart(request)
        context = {"request": request}
        if len(user_cart) > 0:
            data = request.data
            user_address = Address.objects.create(
                street_address=data["street_address"],
                postal_code=data["postal_code"],
                city=data["city"],
                state=data["state"],
                country=data["country"],
            )
            order = Order.objects.create(
                customer=request.user,
                address=user_address
            )
            for item in user_cart:
                product = Product.objects.get(name=item["product"])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item.get("quantity", 1),
                    cost_per_item=item.get("price", product.price),
                )
            user_cart.clear()
            serializer = OrderSerializer(order, context=context)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {"error": "An order can't be created. Your cart is empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class OrderInstance(APIView):

    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk, *args, **kwargs):
        order = Order.objects.filter(customer=request.user, pk=pk).first()
        if order == None:
            raise exceptions.NotFound(
                {"error": "Order with supplied Order ID not found"}
            )
        return order

    def get(self, request, pk, *args, **kwargs):
        order = self.get_object(request, pk=pk)
        context = {"request": request}
        serializer = OrderSerializer(order, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Updates an order with a new address.",
        request_body=AddressSerializer,
        responses={201: OrderSerializer, 400: "Bad Request"},
    )
    def put(self, request, pk, *args, **kwargs):
        order = self.get_object(request, pk=pk)
        context = {"request": request}
        data =  {"address": request.data}
        serializer = OrderSerializer(order, context=context, data=data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, *args, **kwargs):
        order = self.get_object(request, pk=pk)
        order.delete()
        return Response(
            {"message": "Order has been deleted"}, status=status.HTTP_204_NO_CONTENT
        )
