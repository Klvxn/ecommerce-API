from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import exceptions, status
from rest_framework.decorators import api_view
from rest_framework.generics import (
    GenericAPIView,
    ListAPIView,
    RetrieveAPIView,
    get_object_or_404,
)
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Product, Review
from .serializers import (
    CategoryInstanceSerializer,
    CategoryListSerializer,
    ProductInstanceSerializer,
    ProductListSerializer,
    ProductReviewSerializer,
)


# Create your views here.
@extend_schema_view(
    get=extend_schema(
        summary="Get all product categories",
        parameters=[
            OpenApiParameter(
                name="search",
                description="Search categories",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
            )
        ],
        responses={200: CategoryListSerializer(many=True)},
        tags=["Catalogue"],
    )
)
class CategoryListView(ListAPIView):
    """
    View to list products with filtering, searching, and pagination.
    """

    queryset = Category.objects.all()
    permission_classes = [AllowAny]
    serializer_class = CategoryListSerializer
    search_fields = ["name"]


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve a category and its associated products",
        parameters=[
            OpenApiParameter(
                name="search",
                description="Search categories",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
            )
        ],
        responses={
            200: CategoryInstanceSerializer,
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Error: Not found",
                examples=[
                    OpenApiExample(
                        "Not found", value={"detail": "No category matches the given query"}
                    )
                ],
            ),
        },
        tags=["Catalogue"],
    )
)
class CategoryInstanceView(RetrieveAPIView):
    """
    Includes method to retrieve a single product category.
    """

    queryset = Category.objects.all()
    permission_classes = [AllowAny]
    serializer_class = CategoryInstanceSerializer


class ProductListView(GenericAPIView, LimitOffsetPagination):
    """
    View to list products with filtering, searching, and pagination.
    """

    permission_classes = [AllowAny]
    serializer_class = ProductListSerializer
    filterset_fields = ["category", "is_available", "store"]
    search_fields = ["name", "category__name", "label", "store__brand_name"]

    def get_queryset(self):
        queryset = Product.objects.all()
        queryset = self.filter_queryset(queryset)
        return queryset

    @extend_schema(
        summary="Get all available products",
        parameters=[
            OpenApiParameter(
                name="search",
                description="Search products",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
            )
        ],
        responses={200: ProductListSerializer(many=True)},
        tags=["Catalogue"],
    )
    def get(self, request, slug=None):
        products = self.get_queryset()
        page = self.paginate_queryset(products)

        if slug:
            page = self.paginate_queryset(products.filter(category__slug=slug))

        if page is not None:
            serializer = self.get_serializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(products, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        summary="Get a product",
        responses={
            200: ProductInstanceSerializer,
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Error: Not found",
                examples=[
                    OpenApiExample(
                        "Not found", value={"detail": "No category matches the given query"}
                    )
                ],
            ),
        },
        tags=["Catalogue"],
    )
)
class ProductInstanceView(RetrieveAPIView):

    queryset = Product.active_objects.all()
    permission_classes = [AllowAny]
    serializer_class = ProductInstanceSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["product"] = self.get_object()
        return context

@extend_schema(
    summary="Load attributes for a product",
    responses={200: OpenApiResponse(response=OpenApiTypes.ANY)},
    tags=["Catalogue"]
)
@api_view(["GET"])
def load_product_attrs(request, pk):
    product = get_object_or_404(Product, id=pk)
    attrs = product.attributes.values("id", "name")
    resp = [{"id": attr["id"], "name": attr["name"]} for attr in attrs]
    return Response(resp)


@extend_schema_view(
    get=extend_schema(
        summary="Get all reviews for a product",
        responses={200: ProductReviewSerializer(many=True)},
        tags=["Review"],
    ),
    post=extend_schema(
        summary="Add a review for a product",
        request=ProductReviewSerializer,
        responses={
            201: ProductReviewSerializer,
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="Error: Bad request"
            ),
        },
        tags=["Review"],
    ),
)
class ProductReviewView(APIView):
    """
    Handles review actions for products.

    Provides methods to get all reviews for a product and to add a new review.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ProductReviewSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [AllowAny]
        else:
            permission_classes = self.permission_classes
        return [permission() for permission in permission_classes]

    def get(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        serializer = self.get_serializer(product.reviews.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        customer = request.user

        # only customers who purchased a product can post a review for that product
        if product not in customer.products_bought.all():
            return Response(
                {"error": "You can't add a review for a product you didn't purchase."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save(user=request.user, product=product)
            return Response({"success": "Review posted"}, status=status.HTTP_201_CREATED)

        return Response({"error": "Bad request"}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        summary="Get a product's review",
        responses={
            200: ProductReviewSerializer,
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Error: Not found",
                examples=[
                    OpenApiExample(
                        "Not found", value={"detail": "No review matches the given query"}
                    )
                ],
            ),
        },
        tags=["Review"],
    ),
    put=extend_schema(
        summary="Update a product's review",
        responses={
            200: ProductReviewSerializer,
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="Error: Bad request"
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Error: Not found",
                examples=[
                    OpenApiExample(
                        "Not found", value={"detail": "No review matches the given query"}
                    )
                ],
            ),
        },
        tags=["Review"],
    ),
    delete=extend_schema(summary="Delete a product's review", tags=["Review"]),
)
class ProductReviewInstance(APIView):
    """
    View to manage a single product review.
    """

    http_method_names = ["get", "put", "delete"]
    permission_classes = [IsAuthenticated]
    serializer_class = ProductReviewSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [AllowAny]
        else:
            permission_classes = self.permission_classes
        return [permission() for permission in permission_classes]

    def get_product_review(self, product_id, review_id):
        product = get_object_or_404(Product, pk=product_id)
        try:
            return product.reviews.get(pk=review_id)
        except Review.DoesNotExist:
            raise exceptions.NotFound({"error": "Review doesn't exist"})

    def dispatch(self, request, *args, **kwargs):
        # Checks object permissions for PUT and DELETE requests.
        if request.method.lower() in ("put", "delete"):
            self.check_object_permissions(
                request, self.get_product_review(kwargs["product_id"], kwargs["review_id"])
            )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, product_id, review_id):
        review = self.get_product_review(product_id, review_id)
        serializer = self.get_serializer(review)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, product_id, review_id):
        review = self.get_product_review(product_id, review_id)
        serializer = self.get_serializer(instance=review, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response({"error": "Bad request"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, product_id, review_id):
        review = self.get_product_review(product_id, review_id)
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
