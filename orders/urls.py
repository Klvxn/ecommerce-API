from django.urls import path

from .views import OrderInstanceView, OrdersListView, OrderItemView


urlpatterns = [
    path("i/orders/", OrdersListView.as_view(), name="orders"),
    path("i/orders/<uuid:pk>/", OrderInstanceView.as_view(), name="order_detail"),
    path(
        "i/orders/<uuid:order_id>/items/<int:item_id>/",
        OrderItemView.as_view(),
        name="order_item"
    ),
]
