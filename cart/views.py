from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema

from orders.models import Order, OrderItem
from products.models import Product

from .cart import Cart


# Create your views here.
class CartView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_cart = Cart(request)
        if user_cart.cart:
            data = []
            for item in user_cart:
                data.append(item)
            return Response(
                {
                    "Cart Items": data,
                    "Items": len(user_cart),
                    "Total_cost": user_cart.get_total_cost(),
                },
                status=status.HTTP_200_OK,
            )
        return Response({"message": "Your cart is empty"}, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_summary="Creates an order from cart items if 'save_for_later' is true.")
    def post(self, request, *args, **kwargs):
        data = request.data
        action = data.get("save_for_later", False)
        if action:
            order = Order.objects.create(customer=request.user)
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
            return Response(
                {
                    "success": f"Your Order has been saved and your Order ID is {order.id}."
                },
                status=status.HTTP_201_CREATED,
            )

    def put(self, request, *args, **kwargs):
        data = request.data
        user_cart = Cart(request)
        for key, value in data.items():
            product = get_object_or_404(Product, name=key)
            quantity = value["quantity"]
            updated = user_cart.update_item(product, quantity)
            if updated:
                return Response(
                    {"message": "Cart updated"}, status=status.HTTP_202_ACCEPTED
                )

    def delete(self, request, *args, **kwargs):
        data = request.data
        user_cart = Cart(request)
        if data:
            for key in data.keys():
                product = get_object_or_404(Product, name=key)
                removed = user_cart.remove_item(product)
                if removed:
                    return Response(
                        {"message": "Item has been removed from cart"},
                        status=status.HTTP_204_NO_CONTENT,
                    )
        user_cart.clear()
        return Response(
            {"message": "Cart has been cleared"}, status=status.HTTP_204_NO_CONTENT
        )
