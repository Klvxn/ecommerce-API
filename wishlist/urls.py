from django.urls import path

from .views import (
    SharedWishlistView,
    WishlistInstanceView,
    WishlistItemViewSet,
    WishlistListView,
)

urlpatterns = [
    path("wishlists/", WishlistListView.as_view(), name="wishlists"),
    path("wishlists/<int:pk>/", WishlistInstanceView.as_view(), name="wishlist_detail"),
    path("wishlists/shared/<str:sharing_token>/", SharedWishlistView.as_view(), name="shared"),
    path("wishlists/<int:wishlist_pk>/items/", WishlistItemViewSet.as_view()),
]
