from django.urls import path

from .views import CustomerInstance, CustomerCreate


urlpatterns = [
    path("", CustomerCreate.as_view(), name='customers'),
    path("<int:pk>/", CustomerInstance.as_view())
]
