from django.urls import path

from .views import WishlistInstanceView, WishlistListView


urlpatterns = [
    path("wishlists/", WishlistListView.as_view()),
    path("wishlists/<int:pk>/", WishlistInstanceView.as_view(), name="wishlist_detail"),
    path(
        "wishlists/<int:pk>/public/",
        WishlistInstanceView.as_view(),
        name="public_wishlist"
    )
]