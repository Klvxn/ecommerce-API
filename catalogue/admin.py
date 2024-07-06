from django.contrib import admin, messages
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import ngettext

from .models import Category, Product, ProductAttribute, ProductAttributeValue, Review
from .forms import AttributeModelForm, OfferModelForm, VoucherModelForm
from .vouchers.models import Offer, Voucher, RedeemedVoucher


# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}


class AttributeValueInline(admin.TabularInline):

    model = ProductAttributeValue
    min_num = 1
    extra = 2
    fk_name = "attribute"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(
            attribute__product__store__owner=request.user
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return (False
                if not obj
                else obj.product.store.owner == request.user or request.user.is_superuser)

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)

    def has_module_permission(self, request):
        if isinstance(request.user, AnonymousUser):
            return False
        return request.user.is_superuser or request.user.is_vendor


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):

    inlines = [AttributeValueInline]
    form = AttributeModelForm
    list_display = ["name", "product", "attribute_values"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(
            product__store__owner=request.user
        )
    
    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        form.set_current_user(request.user)
        return form

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return (False
                if not obj
                else obj.product.store.owner == request.user or request.user.is_superuser)

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)

    def has_module_permission(self, request):
        if isinstance(request.user, AnonymousUser):
            return False
        return request.user.is_superuser or request.user.is_vendor


class ProductAttributeInline(admin.TabularInline):

    model = ProductAttribute
    min_num = 1
    extra = 2
    fk_name = "product"


class ReviewInline(admin.StackedInline):

    model = Review
    exclude = ["id"]
    readonly_fields = ["user", "review", "image_url", "rating"]
    extra = 0
    fk_name = "product"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    actions = ["make_unavailable"]
    inlines = [ProductAttributeInline, ReviewInline]
    list_display = ["name", "category", "in_stock", "store", "available"]
    readonly_fields = ["rating", "quantity_sold"]
    list_editable = ["category", "available", "in_stock"]
    list_filter = ["available", "category", "created", "store"]
    preserve_filters = True
    search_fields = ["name"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(store__owner=request.user)

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


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):

    list_display = ["__str__", "store", "available_to", "discount_type", "has_expired"]
    readonly_fields = ["store"]
    form = OfferModelForm

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(store__owner=request.user)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        form.set_current_user(request.user)
        return form


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):

    form = VoucherModelForm
    list_display = ["__str__", "code", "offer", "usage_type", "num_of_usage"]
    readonly_fields = ["num_of_usage"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(
            offer__store__owner=request.user
        )

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        form.set_current_user(request.user)
        return form


@admin.register(RedeemedVoucher)
class RedeemedVoucherAdmin(admin.ModelAdmin):

    list_display = ["voucher", "customer", "date_redeemed"]
    readonly_fields = list_display

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(
            voucher__offer__store__owner=request.user
        )
