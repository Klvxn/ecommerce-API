from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import decorators, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Store
from .serializers import StoreInstanceSerializer, StoreSerializer


# Create your views here.
@extend_schema_view(
    list=extend_schema(
        summary="List all active stores",
        parameters=[
            OpenApiParameter(
                name="search",
                description="Search through customer's orders",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            )
        ],
        responses={200: StoreSerializer(many=True)},
        tags=["Store"],
    ),
    retrieve=extend_schema(
        responses={
            200: StoreInstanceSerializer,
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Error: Not found",
                examples=[
                    OpenApiExample(
                        "Not found", value={"detail": "No Store matches the given query"}
                    )
                ],
            ),
        },
        tags=["Store"],
    ),
    create=extend_schema(
        responses={
            201: StoreSerializer,
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="Error: Bad request"
            ),
        },
        tags=["Store"],
    ),
    follow=extend_schema(
        summary="Follow a store",
        responses={200: OpenApiResponse(response=OpenApiTypes.OBJECT)},
        tags=["Store"],
    ),
    unfollow=extend_schema(
        summary="Unfollow a store",
        responses={200: OpenApiResponse(response=OpenApiTypes.OBJECT)},
        tags=["Store"],
    ),
)
class StoreViewSet(ModelViewSet):
    """
    API endpoint for managing stores.

    This viewset provides functionalities for listing, creating, retrieving,
    updating, and deleting a store.
    """

    http_method_names = ["get", "post"]
    lookup_field = "slug"
    queryset = Store.objects.filter(is_active=True)
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = StoreSerializer

    def get_serializer_class(self):
        if self.action == "retrieve":
            return StoreInstanceSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        return serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])

    @decorators.action(["post"], detail=True)
    def follow(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.followers.add(request.user)
        return Response({"success": f"You now follow {instance}"}, status=status.HTTP_200_OK)

    @decorators.action(["post"], detail=True)
    def unfollow(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.followers.remove(request.user)
        return Response({"success": f"You unfollowed {instance}"}, status=status.HTTP_200_OK)
