from django.contrib import admin

from .models import Store


# Register your models here.
@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):

    list_display = ["brand_name", "owner", "products_count", "followers_count"]
    search_fields = ["brand_name", "slug"]
    fields = ["owner", "brand_name", "about", "followers", "address"]
    readonly_fields = ["owner"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(owner=request.user)

    def has_view_permission(self, request, obj=None):
        obj = self.get_queryset(request).first()
        return request.user == obj.owner if obj else False

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        if request.user.is_authenticated:
            if self.model is Store and Store.objects.filter(owner=request.user).exists():
                return True
        return False

    def has_change_permission(self, request, obj=None):
        return request.user == obj.owner if obj else False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return self.has_change_permission(request, obj=obj)
