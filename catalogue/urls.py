from django.urls import path

from .views import (
    ProductCartView,
    ProductsListView,
    ProductReviewView,
    ProductReviewInstance,
    ProductInstanceView,
)

urlpatterns = [
    path("products/", ProductsListView.as_view(), name="products"),
    path("products/categories/<slug:slug>/", ProductsListView.as_view()),
    path("products/<int:pk>/", ProductInstanceView.as_view(), name="product_detail"),
    path("products/<int:pk>/cart/", ProductCartView.as_view()),
    path("products/<int:product_id>/reviews/", ProductReviewView.as_view()),
    path(
        "products/<int:product_id>/reviews/<int:review_id>/",
        ProductReviewInstance.as_view(),
    ),
]
