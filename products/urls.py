from django.urls import path

from .views import APIRoot, ProductInstance, ProductsList


urlpatterns = [
    path("", APIRoot.as_view()),
    path("categories/<slug:slug>/", ProductsList.as_view()),
    path("products/", ProductsList.as_view(), name='products'),
    path("products/<int:pk>/", ProductInstance.as_view()),
]