from django.contrib import admin

from catalogue.admin import ProductInline
from .models import Store


# Register your models here.
@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):

    list_display = ["brand_name", "owner", "slug", "products_count"]
    inlines = [ProductInline]
    search_fields = ["brand_name", "slug"]
