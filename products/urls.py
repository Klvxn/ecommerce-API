from django.urls import path

from .views import ProductInstance, ProductsList


urlpatterns = [
    path("categories/<slug:slug>/", ProductsList.as_view()),
    path("", ProductsList.as_view(), name='products'),
    path("<int:pk>/", ProductInstance.as_view()),
]