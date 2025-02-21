from django.urls import path

from .views import VoucherView


urlpatterns = [path("vouchers/apply/", VoucherView.as_view())]
