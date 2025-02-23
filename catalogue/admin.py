from django.contrib import admin, messages
from django.contrib.admin.options import BaseModelAdmin
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import ngettext

from .models import (
    Category,
    Product,
    Attribute,
    ProductAttribute,
    ProductMedia,
    ProductVariant,
    Review,
    ReviewImage,
    VariantAttribute,
)
from .forms import AttributeModelForm, VariantAttributeInlineForm


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
    form = VariantAttributeInlineForm
    extra = 1
    fk_name = "variant"

    def get_formset(self, request, obj=None, **kwargs):
        """Pass request to form"""
        formset = super().get_formset(request, obj, **kwargs)
        # formset.form.base_fields["attribute"].queryset = ProductAttribute.objects.none()
        return formset


@admin.register(ProductVariant)
class ProductVariantAdmin(SharedPermMixin, admin.ModelAdmin):
    list_display = ["sku", "product", "stock_level", "is_active"]
    inlines = [VariantAttributeInline]
    form = AttributeModelForm
    change_form_template = "admin/change_form_variant.html"
    js = ("catalogue/admin/js/variant.js",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(product__store__owner=request.user)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.set_current_user(request.user)
        print(obj)
        if obj is None:
            # For new variants, add product field with initial value if provided
            if "product" in request.GET:
                form.base_fields["product"].initial = request.GET["product"]
        return form


@admin.register(ProductAttribute)
class ProductAttributeAdmin(SharedPermMixin, admin.ModelAdmin):
    list_display = ["name", "product"]
    # inlines = [VariantAttributeInline]
    form = AttributeModelForm

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(product__store__owner=request.user)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        form.set_current_user(request.user)
        return form


class AttributeInline(admin.TabularInline):
    model = Attribute
    min_num = 1
    extra = 1


class ProductMediaInline(admin.StackedInline):
    model = ProductMedia
    fk_name = "product"
    exclude = ["id"]
    extra = 0
    min_num = 1


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


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    actions = ["make_unavailable"]
    inlines = [ProductMediaInline]
    list_display = ["name", "category", "total_stock_level", "store", "is_available"]
    readonly_fields = ["rating", "total_sold"]
    list_editable = ["category", "is_available", "total_stock_level"]
    list_filter = ["is_available", "category", "created", "store"]
    preserve_filters = True
    search_fields = ["name"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(store__owner=request.user)

    @admin.action(description="Mark selected products as unavailable")
    def make_unavailable(self, request, queryset):
        updated = queryset.update(available=False)
        self.message_user(
            request,
            ngettext(
                f"{updated} product has been marked as unavailable",
                f"{updated} products have been marked as unavailable",
                updated,
            ),
            messages.SUCCESS,
        )


admin.site.register(Attribute)
