from django.urls import path

from .views import OrderInstanceView, OrderListView, OrderItemView


urlpatterns = [
    path("i/orders/", OrderListView.as_view(), name="orders"),
    path("i/orders/<uuid:pk>/", OrderInstanceView.as_view(), name="order_detail"),
    path(
        "i/orders/<uuid:order_id>/items/<int:item_id>/",
        OrderItemView.as_view(),
        name="order_item"
    ),
]
