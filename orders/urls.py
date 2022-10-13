from django.urls import path

from .views import OrderInstance, OrdersList


urlpatterns = [
    path("orders/", OrdersList.as_view(), name="orders"),
    path("orders/<uuid:pk>/", OrderInstance.as_view(), name="order-detail"),
]
