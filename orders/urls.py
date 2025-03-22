from django.urls import path

from .views import CheckoutView, OrderInstanceView, OrderItemView, OrderListView


urlpatterns = [
    path("i/orders/", OrderListView.as_view(), name="orders"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("i/orders/<uuid:pk>/", OrderInstanceView.as_view(), name="order_detail"),
    path(
        "i/orders/<uuid:order_id>/items/<int:item_id>/",
        OrderItemView.as_view(),
        name="order_item"
    ),
]
