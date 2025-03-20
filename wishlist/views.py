from django.utils.text import secrets
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
    get_object_or_404,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import Wishlist, WishlistItem
from .serializers import WishlistItemSerializer, WishlistSerializer


@extend_schema_view(
    get=extend_schema(
        summary="Get all wishlists for the authenticated user",
        parameters=[
            OpenApiParameter(
                name="search",
                description="Search wishlists by name or product name",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            )
        ],
        responses={200: WishlistSerializer(many=True)},
        tags=["Wishlist"],
    ),
    post=extend_schema(
        summary="Create a new wishlist",
        request=WishlistSerializer,
        responses={
            201: WishlistSerializer,
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="Error: Bad request"
            ),
        },
        tags=["Wishlist"],
    ),
)
class WishlistListView(ListCreateAPIView):
    """
    API endpoint for managing a customer's wishlist.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = WishlistSerializer
    search_fields = ["name", "item__product__name"]

    def get_queryset(self):
        queryset = Wishlist.active_objects.filter(owner=self.request.user)
        queryset = self.filter_queryset(queryset)
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


@extend_schema_view(
    get=extend_schema(
        summary="Get a specific wishlist",
        responses={
            200: WishlistSerializer,
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Error: Not found",
                examples=[
                    OpenApiExample(
                        "Not found", value={"detail": "No Wishlist matches the given query"}
                    )
                ],
            ),
        },
        tags=["Wishlist"],
    ),
    put=extend_schema(
        summary="Update wishlist details",
        request=WishlistSerializer,
        responses={
            200: WishlistSerializer,
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="Error: Bad request"
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Error: Not found",
                examples=[
                    OpenApiExample(
                        "Not found", value={"detail": "No Wishlist matches the given query"}
                    )
                ],
            ),
        },
        tags=["Wishlist"],
    ),
    delete=extend_schema(
        summary="Delete wishlist",
        responses={
            204: OpenApiResponse(
                response=OpenApiTypes.NONE, description="Successful, No content"
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Error: Not found",
                examples=[
                    OpenApiExample(
                        "Not found", value={"detail": "No Wishlist matches the given query"}
                    )
                ],
            ),
        },
        tags=["Wishlist"],
    ),
)
class WishlistInstanceView(RetrieveUpdateDestroyAPIView):
    http_method_names = ["get", "put", "delete"]
    queryset = Wishlist.active_objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = WishlistSerializer
    search_fields = ["item__product__name"]

    def get_queryset(self):
        queryset = Wishlist.active_objects.filter(owner=self.request.user)
        # queryset = self.filter_queryset(queryset)
        return queryset

    def perform_update(self, serializer):
        if serializer.validated_data.get("audience") == Wishlist.SHARED:
            serializer.instance.sharing_token = (
                serializer.instance.sharing_token or secrets.token_urlsafe(32)
            )
        serializer.save()


@extend_schema_view(
    retrieve=extend_schema(tags=["Wishlist"]),
    create=extend_schema(tags=["Wishlist"]),
    destroy=extend_schema(tags=["Wishlist"])
)
class WishlistItemViewSet(ModelViewSet):
    http_method_names = ["get", "post", "delete"]
    permission_classes = [IsAuthenticated]
    serializer_class = WishlistItemSerializer

    def get_queryset(self):
        return WishlistItem.objects.filter(
            wishlist_id=self.kwargs["wishlist_id"], wishlist__owner=self.request.user
        )

    def perform_create(self, serializer):
        wishlist = get_object_or_404(
            Wishlist, id=self.kwargs["wishlist_id"], owner=self.request.user
        )
        serializer.save(wishlist=wishlist)


@extend_schema_view(
    get=extend_schema(
        summary="Get a specific wishlist",
        responses={
            200: WishlistSerializer,
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Error: Not found",
                examples=[
                    OpenApiExample(
                        "Not found", value={"detail": "No Wishlist matches the given query"}
                    )
                ],
            ),
        },
        tags=["Wishlist"],
    )
)
class SharedWishlistView(RetrieveAPIView):
    queryset = Wishlist.active_objects.filter(audience=Wishlist.SHARED)
    serializer_class = WishlistSerializer
    permission_classes = [AllowAny]
    lookup_field = "sharing_token"
