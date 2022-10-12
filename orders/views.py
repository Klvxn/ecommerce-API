from rest_framework import exceptions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.cart import Cart
from customers.models import Address
from products.models import Product

from .models import Order, OrderItem
from .serializers import OrderSerializer


# Create your views here.
class OrdersList(APIView):

    permission_classes = [IsAuthenticated]

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

    def post(self, request, *args, **kwargs):
        user_cart = Cart(request)
        order = Order.objects.create(
            customer=request.user,
            address=Address.objects.create(
                street_address="195 ifite road",
                zip_code=123412,
                city="Awka",
                state="Anambra",
            ),
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
            {"message": f"Order has been deleted"},
            status=status.HTTP_204_NO_CONTENT,
        )
