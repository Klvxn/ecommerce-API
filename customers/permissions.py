from rest_framework.permissions import BasePermission


class CustomerOnly(BasePermission):

    def has_object_permission(self, request, view, obj):
        return request.user == obj 
