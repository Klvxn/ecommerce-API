from django.urls import path

from .views import OrderInstanceView, OrdersListView


urlpatterns = [
    path("i/orders/", OrdersListView.as_view(), name="orders"),
    path("i/orders/<uuid:pk>/", OrderInstanceView.as_view(), name="order-detail"),
]
