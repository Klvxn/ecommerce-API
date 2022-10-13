from rest_framework import exceptions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from cart.cart import Cart
from customers.models import Address
from customers.serializers import AddressSerializer
from products.models import Product

from .models import Order, OrderItem
from .serializers import OrderSerializer


# Create your views here.
class OrdersList(APIView):

    permission_classes = [IsAuthenticated]

    order_status = openapi.Parameter("status", in_=openapi.IN_QUERY, type=openapi.TYPE_STRING)
    @swagger_auto_schema(manual_parameters=[order_status])
    def get(self, request, *args, **kwargs):
        customer = request.user
        if request.query_params:
            query = request.query_params.get("status")
            orders = Order.objects.filter(customer=customer, status=query)
            serializer = OrderSerializer(orders, many=True, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        orders = Order.objects.filter(customer=customer)
        serializer = OrderSerializer(orders, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Creates an order from cart items.",
        request_body=AddressSerializer,
        responses={201: OrderSerializer},
    )
    def post(self, request, *args, **kwargs):
        data = request.data
        order = Order.objects.create(
            customer=request.user,
            address=Address.objects.create(
                street_address=data["street_address"],
                postal_code=data["postal_code"],
                city=data["city"],
                state=data["state"],
                country=data["country"],
            ),
        )
        user_cart = Cart(request)
        for item in user_cart:
            product = Product.objects.get(name=item["product"])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item.get("quantity", 1),
                cost_per_item=item.get("price", product.price),
            )
        user_cart.clear()
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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
        serializer = OrderSerializer(order, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk, *args, **kwargs):
        order = self.get_object(request, pk=pk)
        order.delete()
        return Response(
            {"message": f"Order has been deleted"}, status=status.HTTP_204_NO_CONTENT
        )
