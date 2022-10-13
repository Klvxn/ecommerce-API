from django.urls import path

from .views import OrderInstance, OrdersList


urlpatterns = [
    path("", OrdersList.as_view(), name="orders"),
    path("<uuid:pk>/", OrderInstance.as_view(), name="order-detail"),
]
