from django.contrib import admin, messages
from django.utils.translation import ngettext

from .models import Category, Product, Review


# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}


class ReviewInline(admin.TabularInline):

    model = Review
    extra = 0
    

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    actions = ["make_unavailable"]
    inlines = [ReviewInline]
    list_display = ["name", "category", "stock", "price", "available"]
    list_editable = ["category", "available", "stock", "price"]
    list_filter = ["category", "available"]
    preserve_filters = True
    search_fields = ["name"]

    @admin.action(description='Mark selected products as unavailable')
    def make_unavailable(self, request, queryset):
        updated = queryset.update(available=False)
        self.message_user(
            request,
            ngettext(
                f"{updated} product has been marked as unavailable", 
                f"{updated} products have been marked as unavailable", 
                updated
            ), 
            messages.SUCCESS
        )
