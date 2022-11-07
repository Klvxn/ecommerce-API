from django.urls import path

from .views import VendorCreate, VendorInstance


urlpatterns = [
    path("vendors/", VendorCreate.as_view(), name="vendor"),
    path("vendors/<slug:slug>/", VendorInstance.as_view(), name="vendor")
]
