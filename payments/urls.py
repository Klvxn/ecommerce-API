from django.urls import path

from .views import Payment


urlpatterns = [
    path("i/orders/<uuid:pk>/checkout/", Payment.as_view(), name='payment'),
]