from django.urls import path

from .views import CartItemView, CartView


urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/items/<str:item_key>/", CartItemView.as_view()),
]
