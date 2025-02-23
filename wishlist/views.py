from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from rest_framework import status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Wishlist, Product
from .serializers import WishlistSerializer


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
class WishlistListView(GenericAPIView):
    """
    API endpoint for managing a customer's wishlist.
    """

    http_method_names = ["get", "post"]
    permission_classes = [IsAuthenticated]
    serializer_class = WishlistSerializer
    search_fields = ["name", "item__product__name"]

    def get_queryset(self):
        queryset = Wishlist.objects.filter(owner=self.request.user)
        queryset = self.filter_queryset(queryset)
        return queryset

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        context = self.get_serializer_context()
        context["owner"] = request.user
        serializer = self.get_serializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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
            401: None,
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
            OpenApiExample("Delete Wishlist", value={}, description="Delete the entire wishlist"),
        ],
        tags=["Wishlist"],
    ),
)
class WishlistInstanceView(GenericAPIView):
    queryset = Wishlist.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = WishlistSerializer
    search_fields = ["item__product__name"]

    def get_queryset(self):
        queryset = Wishlist.objects.filter(owner=self.request.user)
        queryset = self.filter_queryset(queryset)
        return queryset

    def dispatch(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_private:
            self.check_object_permissions(request, instance)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, pk):
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"error": "Product is required"}, status=status.HTTP_400_BAD_REQUEST)
        product = get_object_or_404(Product, pk=product_id)
        self.get_object().add(product)
        return Response(status=status.HTTP_201_CREATED)

    def put(self, request, pk):
        serializer = self.get_serializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        product_id = request.data.get("product_id")
        if not product_id:
            self.get_object().delete()
        else:
            product = get_object_or_404(Product, pk=product_id)
            self.get_object().remove(product)
        return Response(status=status.HTTP_204_NO_CONTENT)
