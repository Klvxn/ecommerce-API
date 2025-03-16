from django.contrib import admin

from .models import Store


# Register your models here.
@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "products_count", "followers_count"]
    search_fields = ["name", "slug"]
    fields = ["owner", "name", "about", "followers", "address"]
    readonly_fields = ["owner"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(owner=request.user)

    def has_view_permission(self, request, obj=None):
        obj = self.get_queryset(request).first()
        if obj:
            return (
                request.user == obj.owner or request.user.is_superuser or request.user.is_staff
            )
        return request.user.is_superuser or request.user.is_staff

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        if request.user.is_authenticated:
            if self.model is Store and Store.objects.filter(owner=request.user).exists():
                return True
        return False

    def has_change_permission(self, request, obj=None):
        obj = self.get_queryset(request).first()
        if obj:
            return request.user == obj.owner or request.user.is_superuser
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj=obj)
