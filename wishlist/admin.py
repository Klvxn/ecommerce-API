from django.contrib import admin

from .models import Wishlist, WishlistItem


# Register your models here.
class WishlistItemInline(admin.TabularInline):

    model = WishlistItem
    extra = 0
    fk_name = "wishlist"


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):

    list_display = ("__str__", "owner", "audience")
    inlines = [WishlistItemInline]
