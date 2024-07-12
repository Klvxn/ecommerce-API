import braintree
from django.conf import settings
from django.db import transaction
from django.template.response import TemplateResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from orders.serializers import OrderSerializer
from .models import Transaction
from .tasks import send_order_confirmation_email, write_trxn_to_csv, update_stock


# Create your views here.
gateway = braintree.BraintreeGateway(settings.BRAINTREE_CONF)


class Payment(APIView):

    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        order = Order.objects.select_related("customer", "address")
        return get_object_or_404(order, customer=self.request.user, pk=pk)

    @swagger_auto_schema(tags=["Payment"])
    def get(self, request, pk):
        order = self.get_object(pk)
        serializer = OrderSerializer(order, context={"request": request})
        # client_token = gateway.client_token.generate()
        context = {"client_token": "client_token", "order": serializer.data}
        return TemplateResponse(request, "payment.html", context)

    @swagger_auto_schema(tags=["Payment"])
    def post(self, request, pk):
        order = self.get_object(pk)
        customer = order.customer
        address = order.address
        total_cost = order.total_cost()
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
            with transaction.atomic():
                order.status = "paid"
                order.save()
                update_stock.delay(order, customer)
                send_order_confirmation_email.delay(order)
                write_trxn_to_csv.delay(order, customer, result.transaction.id)
                Transaction.objects.create(
                    order=order,
                    customer=order.customer,
                    transaction_id=result.transaction.id,
                    amount_paid=total_cost
                )
                return Response(
                    {"success": "Payment was successful"}, status=status.HTTP_200_OK
                )
        return Response(
            {"error": f"{result.message}"}, status=status.HTTP_502_BAD_GATEWAY
        )
