from django.urls import path

from .views import ProductInstance, ProductsList, ReviewActions, ReviewInstance


urlpatterns = [
    path("products/categories/<slug:slug>/", ProductsList.as_view()),
    path("products/", ProductsList.as_view(), name="products"),
    path("products/<int:pk>/", ProductInstance.as_view(http_method_names=["get"])),
    path("products/<int:pk>/add/", ProductInstance.as_view(http_method_names=["post"])),
    path("products/<int:pk>/remove/", ProductInstance.as_view(http_method_names=["delete"])),
    path(
        "products/<int:product_id>/customer-reviews/",
        ReviewActions.as_view(http_method_names=["get", "post"])
    ),
    path(
        "products/<int:product_id>/customer-reviews/<int:review_id>/",
        ReviewInstance.as_view(http_method_names=["get"])
    ),
    path(
        "products/<int:product_id>/customer-reviews/<int:review_id>/update/",
        ReviewInstance.as_view(http_method_names=["put"])
    ),
    path(
        "products/<int:product_id>/customer-reviews/<int:review_id>/delete/",
        ReviewInstance.as_view(http_method_names=["delete"])
    ),
]
