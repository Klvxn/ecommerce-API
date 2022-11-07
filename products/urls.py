from django.urls import path

from .views import ProductInstance, ProductsList


urlpatterns = [
    path("products/categories/<slug:slug>/", ProductsList.as_view()),
    path("products/", ProductsList.as_view(), name="products"),
    path("products/<int:pk>/", ProductInstance.as_view()),
]
