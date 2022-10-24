from django.urls import path

from .views import ProductInstance, ProductsList, VendorInstance


urlpatterns = [
    path("products/categories/<slug:slug>/", ProductsList.as_view()),
    path("products/", ProductsList.as_view(), name="products"),
    path("products/<int:pk>/", ProductInstance.as_view()),
    path("vendors/<slug:slug>/", VendorInstance.as_view(), name="vendor"),
]
