from django.utils.text import secrets
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
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
        responses={200: WishlistSerializer(many=True), 401: None},
        tags=["Wishlist"],
    ),
    post=extend_schema(
        summary="Create a new wishlist",
        request=WishlistSerializer,
        responses={201: WishlistSerializer, 400: None, 401: None},
        tags=["Wishlist"],
    ),
)
class WishlistListView(ListCreateAPIView):
    """
    API endpoint for managing a customer's wishlist.
    """

    http_method_names = ["get", "post"]
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
        responses={200: WishlistSerializer, 401: None, 403: None, 404: None},
        tags=["Wishlist"],
    ),
    post=extend_schema(
        summary="Add a product to wishlist",
        request={
            "application/json": {
                "type": "object",
                "properties": {"product_id": {"type": "integer"}},
                "required": ["product_id"],
            }
        },
        responses={
            201: None,
            400: {"type": "object", "properties": {"error": {"type": "string"}}},
            404: None,
        },
        examples=[
            OpenApiExample(
                "Valid Request",
                value={"product_id": 1},
                description="Add product with ID 1 to the wishlist",
            )
        ],
        tags=["Wishlist"],
    ),
    put=extend_schema(
        summary="Update wishlist details",
        request=WishlistSerializer,
        responses={201: WishlistSerializer, 400: None, 401: None, 404: None},
        tags=["Wishlist"],
    ),
    delete=extend_schema(
        summary="Delete wishlist or remove product",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer"},
                },
            }
        },
        responses={204: None, 401: None, 404: None},
        examples=[
            OpenApiExample(
                "Remove Product",
                value={"product_id": 1},
                description="Remove product with ID 1 from the wishlist",
            ),
            OpenApiExample(
                "Delete Wishlist", value={}, description="Delete the entire wishlist"
            ),
        ],
        tags=["Wishlist"],
    ),
)
class WishlistInstanceView(RetrieveUpdateDestroyAPIView):
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


class WishlistItemViewSet(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WishlistItemSerializer

    def get_queryset(self):
        return WishlistItem.objects.filter(
            wishlist_id=self.kwargs["wishlist_pk"], wishlist__owner=self.request.user
        )

    def perform_create(self, serializer):
        wishlist = get_object_or_404(
            Wishlist, id=self.kwargs["wishlist_pk"], owner=self.request.user
        )
        serializer.save(wishlist=wishlist)


class SharedWishlistView(RetrieveAPIView):
    queryset = Wishlist.active_objects.filter(audience=Wishlist.SHARED)
    serializer_class = WishlistSerializer
    permission_classes = [AllowAny]
    lookup_field = "sharing_token"
