from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import exceptions, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import LimitOffsetPagination
from cart.cart import Cart

from .models import Product
from .serializers import ProductInstanceSerializer, ProductReviewSerializer, ProductsSerializer


# Create your views here.
class ProductsList(GenericAPIView, LimitOffsetPagination):

    permission_classes = [AllowAny]
    serializer_class = ProductsSerializer
    filterset_fields = ['category', 'available', 'vendor']
    search_fields = ['name', 'category__name', 'label', 'vendor__brand_name']

    def get_queryset(self):
        queryset = Product.objects.all()
        queryset = self.filter_queryset(queryset)
        return queryset

    @swagger_auto_schema(
        operation_summary="Get all available products",
        manual_parameters=[
            openapi.Parameter(
                name="search", in_=openapi.IN_QUERY, type=openapi.TYPE_STRING
            )
        ],
        responses={200: ProductsSerializer(many=True)},
        tags=["products"],
    )
    def get(self, request, slug=None):
        products = self.get_queryset()
        page = self.paginate_queryset(products)

        if slug:
            page = self.paginate_queryset(
                products.filter(category__slug=slug)
            )

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductInstance(GenericAPIView):

    queryset = Product.objects.all()
    permission_classes = [AllowAny]
    serializer_class = ProductInstanceSerializer

    def get_object(self):
        try:
            return super().get_object()
        except Product.DoesNotExist:
            raise exceptions.NotFound({"error": "Product not found."})

    @swagger_auto_schema(operation_summary="Retrieve a product", tags=["products"])
    def get(self, request, pk):
        product = self.get_object()
        serializer = self.get_serializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Add a product to cart",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            default=1,
            properties={
                "quantity": openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            example={"quantity": 12},
        ),
        tags=["products"],
    )
    def post(self, request, pk):
        product = self.get_object()
        user_cart = Cart(request)
        quantity = request.data.get("quantity")

        if quantity > product.stock:
            return Response(
                {"error": "The quantity cannot be more than product's stock"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_cart.add_item(product=product, quantity=quantity)
        return Response(
            {"success": f"{product} has been added to cart"},
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        operation_summary="Delete a product from cart", tags=["products"]
    )
    def delete(self, request, pk):
        product = self.get_object()
        user_cart = Cart(request)
        deleted = user_cart.remove_item(product)

        if deleted:
            return Response(
                {"message": f"{product} has been removed from cart."},
                status=status.HTTP_204_NO_CONTENT,
            )

        return Response(
            {"message": f"{product} is not in cart."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ReviewActions(GenericAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = ProductReviewSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [AllowAny]
        else:
            permission_classes = self.permission_classes
        return [permission() for permission in permission_classes]

    @swagger_auto_schema(
        operation_summary="Get all product reviews",
        extra_overrides="get",
        tags=["reviews"]
    )
    def get(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        serializer = self.get_serializer(product.reviews.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Add a product review",
        tags=["reviews"]
    )
    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        customer = request.user

        if product not in customer.products_bought.all():
            return Response(
                {"message": "You can't add a review for a product you didn't purchase."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save(user=request.user, product=product)
            return Response(
                {"message": "Review posted"}, status=status.HTTP_201_CREATED
            )

        return Response(
            {"message": "Bad request"}, status=status.HTTP_400_BAD_REQUEST
        )


class ReviewInstance(GenericAPIView):

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
        return product.reviews.get(pk=review_id)

    @swagger_auto_schema(
        operation_summary="Get a product's review",
        tags=["reviews"]
    )
    def get(self, request, product_id, review_id):
        review = self.get_product_review(product_id, review_id)
        serializer = self.get_serializer(review)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Update a product's review",
        tags=["reviews"]
    )
    def put(self, request, product_id, review_id):
        review = self.get_product_review(product_id, review_id)

        if request.user != review.user:
            return Response(
                {"message": "Access forbidden"}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(instance=review, data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            {"message": "Bad request"}, status=status.HTTP_400_BAD_REQUEST
        )

    @swagger_auto_schema(
        operation_summary="Delete a product's review",
        tags=["reviews"]
    )
    def delete(self, request, product_id, review_id):
        review = self.get_product_review(product_id, review_id)

        if request.user != review.user:
            return Response(
                {"message": "Access forbidden"}, status=status.HTTP_403_FORBIDDEN
            )

        review.delete()
        return Response(
            {"message": "Review deleted"}, status=status.HTTP_204_NO_CONTENT
        )
