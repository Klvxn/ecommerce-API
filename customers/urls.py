from django.urls import path

from .views import CustomerInstance, CustomerCreate


urlpatterns = [
    path("customers/", CustomerCreate.as_view(), name='customers'),
    path("customers/<int:pk>/", CustomerInstance.as_view())
]
