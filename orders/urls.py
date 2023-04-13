from django.urls import path

from .views import OrderInstanceView, OrdersListView


urlpatterns = [
    path("me/orders/", OrdersListView.as_view(), name="orders"),
    path("me/orders/<uuid:pk>/", OrderInstanceView.as_view(), name="order-detail"),
]
