from rest_framework.permissions import BasePermission


class StoreOwnerOnly(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated and request.user.is_vendor:
            return bool(request.user == obj.owner)
