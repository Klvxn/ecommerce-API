from django.urls import path

from .views import WishlistInstanceView, WishlistListView


urlpatterns = [
    path("wishlists/", WishlistListView.as_view(), name="wishlists"),
    path("wishlists/<int:pk>/", WishlistInstanceView.as_view(), name="wishlist_detail"),
    path("wishlists/shared/<str:token>/", WishlistInstanceView.as_view(), name="shared"),
    path(
        "wishlists/<int:pk>/public/",
        WishlistInstanceView.as_view(),
        name="public_wishlist"
    )
]
