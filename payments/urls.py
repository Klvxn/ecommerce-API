from django.urls import path

from .views import Payment


urlpatterns = [
    path("payments/checkout/order/<uuid:pk>/", Payment.as_view(), name='payment'),
]