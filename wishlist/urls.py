from django.urls import path

from .views import WishlistInstanceView, WishlistView


urlpatterns = [
    path("wishlists/", WishlistView.as_view()),
    path("wishlists/<int:pk>/", WishlistInstanceView.as_view()),
    path(
        "wishlists/<int:pk>/public/",
        WishlistInstanceView.as_view(),
        name="public_wishlist"
    )
]