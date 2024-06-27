from rest_framework.permissions import BasePermission


class VendorOnly(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated and request.user.is_vendor:
            return bool(request.user == obj.owner)


class VendorCreateOnly(BasePermission):

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.is_vendor)
