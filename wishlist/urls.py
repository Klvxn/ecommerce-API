from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (
    SharedWishlistView,
    WishlistInstanceView,
    WishlistItemViewSet,
    WishlistListView,
)


router = SimpleRouter()
router.register("wishlist_items", WishlistItemViewSet, basename="items")

urlpatterns = [
    path("wishlists/", WishlistListView.as_view(), name="wishlists"),
    path("wishlists/<int:pk>/", WishlistInstanceView.as_view(), name="wishlist_detail"),
    path("wishlists/shared/<str:sharing_token>/", SharedWishlistView.as_view(), name="shared"),
    path("wishlists/<int:wishlist_id>/", include(router.urls)),
]
