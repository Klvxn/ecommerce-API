from rest_framework import decorators, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Store
from .permissions import StoreOwnerOnly
from .serializers import StoreInstanceSerializer, StoreSerializer


# Create your views here.
class StoreViewSet(ModelViewSet):
    """
    API endpoint for managing stores.

    This viewset provides functionalities for listing, creating, retrieving,
    updating, and deleting a store.
    """

    http_method_names = ["get", "post", "put", "delete"]
    lookup_field = "slug"
    queryset = Store.objects.filter(is_active=True)
    permission_classes = [StoreOwnerOnly, IsAuthenticated]
    serializer_class = StoreSerializer

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [IsAuthenticated]
        elif self.action in ["update", "destroy"]:
            permission_classes = [StoreOwnerOnly]
        else:
            permission_classes = [AllowAny]

        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return StoreInstanceSerializer
        return super().get_serializer_class()

    def dispatch(self, request, *args, **kwargs):
        if request.method in ("put", "patch", "delete"):
            self.check_object_permissions(request, self.get_object())
        return super().dispatch(request,*args, **kwargs)

    def perform_create(self, serializer):
        return serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])

    @decorators.action(["post"], detail=True)
    def follow_store(self, request, pk):
        instance = self.get_object()
        instance.followers.add(request.user)
        return Response(
            {"success": f"You now follow {instance}"}, status=status.HTTP_200_OK
        )

    @decorators.action(["post"], detail=True)
    def unfollow_store(self, request, pk):
        instance = self.get_object()
        instance.followers.remove(request.user)
        return Response(
            {"success": f"You unfollowed {instance}"}, status=status.HTTP_200_OK
        )
