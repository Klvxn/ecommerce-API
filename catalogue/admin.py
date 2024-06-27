from django.contrib import admin, messages
from django.utils.translation import ngettext

from .models import Category, Product, ProductAttribute, ProductAttributeValue, Review
from .vouchers.models import Offer, Voucher, RedeemedVoucher


# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}


class ReviewInline(admin.TabularInline):

    model = Review
    extra = 0
    fk_name = "product"


class AttributeValueInline(admin.TabularInline):

    model = ProductAttributeValue
    extra = 0
    fk_name = "attribute"


@admin.register(ProductAttribute)
class ProductAttribute(admin.ModelAdmin):

    inlines = [AttributeValueInline]
    list_display = ["name", "product"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    actions = ["make_unavailable"]
    inlines = [ReviewInline]
    list_display = ["name", "category", "in_stock", "price", "available"]
    list_editable = ["category", "available", "in_stock", "price"]
    list_filter = ["available", "category", "created", "store"]
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


class ProductInline(admin.StackedInline):

    model = Product
    extra = 0
    raw_id_fields = ["store"]


admin.site.register(Offer)
admin.site.register(Voucher)
admin.site.register(RedeemedVoucher)
