from django.urls import path

from .views import OfferView


urlpatterns = [
    path("offers/", OfferView.as_view(), name="offers"),
]
