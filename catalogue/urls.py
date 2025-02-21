from django.urls import path

from .views import (
    CategoryInstanceView,
    CategoryListView,
    ProductInstanceView,
    ProductListView,
    ProductReviewView,
    ProductReviewInstance,
    load_product_attrs,
)

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("categories/<slug:slug>/", CategoryInstanceView.as_view(), name="products"),
    path("products/", ProductListView.as_view(), name="products"),
    path("products/categories/<slug:slug>/", ProductListView.as_view()),
    path("products/<int:pk>/", ProductInstanceView.as_view(), name="product_detail"),
    path("products/<int:pk>/attributes/", load_product_attrs, name="product_attrs"),
    path("products/<int:product_id>/reviews/", ProductReviewView.as_view()),
    path(
        "products/<int:product_id>/reviews/<int:review_id>/",
        ProductReviewInstance.as_view(),
    ),
]
