from django.urls import path

from .views import OrderInstance, OrdersList


urlpatterns = [
    path("me/orders/", OrdersList.as_view(), name="orders"),
    path("me/orders/<uuid:pk>/", OrderInstance.as_view(), name="order-detail"),
]
