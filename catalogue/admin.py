from django.contrib import admin, messages
from django.contrib.admin.options import BaseModelAdmin
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import ngettext

from .models import (
    Attribute,
    Category,
    Product,
    ProductMedia,
    ProductVariant,
    Review,
    ReviewImage,
    VariantAttribute,
)


# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}


class SharedPermMixin(BaseModelAdmin):
    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return False if not obj else obj.product.store.owner == request.user or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)

    def has_module_permission(self, request):
        if isinstance(request.user, AnonymousUser):
            return False
        return request.user.is_superuser or request.user.is_vendor


class VariantAttributeInline(admin.TabularInline, SharedPermMixin):
    model = VariantAttribute
    extra = 1
    fk_name = "variant"


@admin.register(ProductVariant)
class ProductVariantAdmin(SharedPermMixin, admin.ModelAdmin):
    list_display = ["sku", "product", "get_attribute_combination", "is_active"]
    inlines = [VariantAttributeInline]
    change_form_template = "admin/change_form_variant.html"
    js = ("catalogue/admin/js/variant.js",)

    @admin.display(description="attribute combination")
    def get_attribute_combination(self, obj):
        return obj

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(product__store__owner=request.user)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # form.set_current_user(request.user)
        if obj is None:
            # For new variants, add product field with initial value if provided
            if "product" in request.GET:
                form.base_fields["product"].initial = request.GET["product"]
        return form


class ReviewImageInline(admin.StackedInline):
    model = ReviewImage
    fk_name = "review"
    exclude = ["id"]
    extra = 0
    min_num = 1


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    model = Review
    exclude = ["id"]
    list_display = ["__str__", "product", "created", "rating"]
    inlines = [ReviewImageInline]
    # readonly_fields = ["user", "review", "rating"]
    extra = 0

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(product__store__owner=request.user)


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    fk_name = "product"
    exclude = ["id"]
    extra = 0
    min_num = 1


class AttributeInline(admin.TabularInline):
    model = Attribute
    fk_name = "product"
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    actions = ["make_inactive"]
    inlines = [ProductMediaInline, AttributeInline]
    list_display = ["name", "category", "store", "is_active"]
    readonly_fields = ["rating", "total_sold"]
    list_editable = ["is_active"]
    list_filter = ["is_active", "category", "created", "store"]
    preserve_filters = True
    search_fields = ["name"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(store__owner=request.user)

    @admin.action(description="Mark selected products as inactive")
    def make_inactive(self, request, queryset):
        updated = queryset.update(available=False)
        self.message_user(
            request,
            ngettext(
                f"{updated} product has been marked as inactive",
                f"{updated} products have been marked as inactive",
                updated,
            ),
            messages.SUCCESS,
        )


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_global", "product")
