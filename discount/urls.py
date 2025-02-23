from django.urls import path

from .views import OfferView, VoucherView


urlpatterns = [
    path("vouchers/apply/", VoucherView.as_view()),
    path("offers/", OfferView.as_view(), name="offers"),
]
