from django.urls import path

from .views import CartView


urlpatterns = [
    path("shopping-cart/", CartView.as_view(), name='cart')
]
