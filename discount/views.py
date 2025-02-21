from rest_framework.generics import RetrieveAPIView
from rest_framework.mixins import CreateModelMixin
from rest_framework.response import Response
from rest_framework import status

from cart.cart import Cart
from .models import Voucher
from .serializers import VoucherSerializer


# Create your views here.
class VoucherView(CreateModelMixin, RetrieveAPIView):
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer
    http_method_names = ["post"]
    lookup_field = "code"

    def post(self, request):
        """
        Apply voucher code to a customer's order
        """
        voucher = self.get_object()
        cart = Cart(request)
        customer = request.user

        order_value = cart.total()
        is_valid, error_msg = voucher.is_valid(customer, order_value)
        if not is_valid:
            return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)

        voucher_offer = voucher.offer
        new_total = voucher_offer.apply_discount(order_value)

        # cart['total'] = new_total
        return Response(new_total)
