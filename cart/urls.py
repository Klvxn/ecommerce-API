from django.urls import path

from .views import CartItemView, CartView, CartVoucherView

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/items/", CartItemView.as_view()),
    path("cart/apply/vouchers/", CartVoucherView.as_view()),
]
