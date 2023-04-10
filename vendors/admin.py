from django.contrib import admin

from products.admin import ProductInline
from .models import Vendor


# Register your models here.
@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):

    list_display = ["brand_name", "customer", "slug", "products_count"]
    inlines = [ProductInline]
    search_fields = ["brand_name", "slug"]
