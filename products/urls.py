from django.urls import path

from .views import (
    ProductCartView,
    ProductsListView,
    ReviewActions,
    ReviewInstance,
    ProductCRUDView,
)

urlpatterns = [
    path("products/", ProductsListView.as_view(), name="products"),
    path("products/categories/<slug:slug>/", ProductsListView.as_view()),
    path("products/create/", ProductCRUDView.as_view(http_method_names=["post"])),
    path(
        "products/<int:pk>/",
        ProductCRUDView.as_view(http_method_names=["get", "put", "delete"]),
    ),
    path("products/<int:pk>/cart/", ProductCartView.as_view()),
    path(
        "products/<int:product_id>/reviews/",
        ReviewActions.as_view(),
    ),
    path(
        "products/<int:product_id>/reviews/<int:review_id>/",
        ReviewInstance.as_view(),
    ),
]
