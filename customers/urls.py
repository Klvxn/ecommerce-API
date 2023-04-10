from django.urls import path

from .views import CustomerInstanceView, CustomerCreateView

urlpatterns = [
    path("customers/", CustomerCreateView.as_view(), name='customers'),
    path("customers/<int:pk>/", CustomerInstanceView.as_view()),
]
