from django.urls import path

from .views import Payment


urlpatterns = [
    path("checkout/order/<uuid:pk>/", Payment.as_view(), name='payment'),
]