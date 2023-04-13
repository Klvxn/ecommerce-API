import braintree, json
from django.conf import settings
from django.template.response import TemplateResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import exceptions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from orders.serializers import SimpleOrderSerializer
from products.models import Product

from .tasks import send_order_confirmation_email, write_trxn_to_csv


# Create your views here.
gateway = braintree.BraintreeGateway(settings.BRAINTREE_CONF)


class Payment(APIView):

    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            order = Order.objects.select_related("customer", "address").get(customer=self.request.user, pk=pk)
            return order
        except Order.DoesNotExist:
            raise exceptions.NotFound("Order with ID not found")

    @swagger_auto_schema(tags=["payment"])
    def get(self, request, pk):
        order = self.get_object(pk)
        serializer = SimpleOrderSerializer(order)
        data = serializer.data
        data["address"] = json.dumps(data["address"])
        data["order_items"] = json.dumps(data["order_items"])
        client_token = gateway.client_token.generate()
        context = {"client_token": client_token, "order": data.items()}
        return TemplateResponse(request, "payment.html", context)

    @swagger_auto_schema(tags=["payment"])
    def post(self, request, pk):
        order = self.get_object(pk)
        customer = order.customer
        address = order.address
        total_cost = order.get_total_cost()
        customer_kwargs = {
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "street_address": address.street_address,
            "postal_code": str(address.postal_code),
            "locality": address.city,
            "region": address.state,
            "country_name": address.country,
        }
        nonce_from_client = request.data["payment_method_nonce"]
        result = gateway.transaction.sale(
            {
                "amount": f"{total_cost:.2f}",
                "payment_method_nonce": nonce_from_client,
                "shipping": {**customer_kwargs},
                "options": {
                    "submit_for_settlement": True,
                    "store_in_vault_on_success": True,
                },
            }
        )

        if result.is_success:
            order.status = "paid"
            order.save()

            for item in order.order_items.all().select_related('product'):
                product = Product.objects.filter(id=item.product_id)
                product.update(stock=item.product.stock - item.quantity, sold=item.quantity)
                customer.total_items_bought += item.quantity
                customer.products_bought.add(product)
                customer.save()

                for obj in product:
                    obj.save()

            send_order_confirmation_email.delay(order)
            write_trxn_to_csv.delay(order, customer, result.transaction.id)
            return Response(
                {"success": "Payment was successful"}, status=status.HTTP_200_OK
            )

        return Response(
            {"error": f"{result.message}"}, status=status.HTTP_502_BAD_GATEWAY
        )
