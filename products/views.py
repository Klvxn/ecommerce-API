from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import exceptions, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.pagination import LimitOffsetPagination

from cart.cart import Cart
from vendors.permissions import VendorCreateOnly, VendorOnly

from .models import Discount, Product, Review
from .serializers import (
    ProductInstanceSerializer,
    ProductReviewSerializer,
    ProductsListSerializer,
    ProductCreateUpdateSerializer,
    DiscountSerializer,
)


# Create your views here.
class DiscountView(ListAPIView):
    
    serializer_class = DiscountSerializer
    queryset = Discount.objects.all()
    permission_classes = [AllowAny]


class ProductsListView(GenericAPIView, LimitOffsetPagination):
    """
    View to list products with filtering, searching, and pagination.
    """
    permission_classes = [AllowAny]
    serializer_class = ProductsListSerializer
    filterset_fields = ["category", "available", "vendor"]
    search_fields = ["name", "category__name", "label", "vendor__brand_name"]

    def get_queryset(self):
        queryset = Product.objects.all()
        queryset = self.filter_queryset(queryset)
        return queryset

    @swagger_auto_schema(
        operation_summary="Get all available products",
        manual_parameters=[
            openapi.Parameter(
                name="search", 
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Search products"
            )
        ],
        responses={200: ProductsListSerializer(many=True)},
        tags=["products"],
    )
    def get(self, request, slug=None):
        products = self.get_queryset()
        page = self.paginate_queryset(products)

        if slug:
            page = self.paginate_queryset(products.filter(category__slug=slug))

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductCRUDView(GenericAPIView):
    """
    Includes methods to create, retrieve, update and delete a product.

    The `post`, `put`, and `delete` methods are permitted to vendors only
    """

    queryset = Product.objects.all()
    permission_classes = [IsAuthenticated, VendorOnly]

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [AllowAny]
        elif self.request.method == "POST":
            permission_classes = [VendorCreateOnly]
        else:
            permission_classes = self.permission_classes
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.request.method == "GET":
            serializer_class = ProductInstanceSerializer
        else:
            serializer_class = ProductCreateUpdateSerializer
        return serializer_class

    @swagger_auto_schema(operation_summary="Retrieve a product", tags=["products"])
    def get(self, request, pk):
        product = self.get_object()
        serializer = self.get_serializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_summary="Create a product", tags=["products"])
    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save(vendor=request.user.vendor)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(operation_summary="Update a product", tags=["products"])
    def put(self, request, pk):
        product = self.get_object()
        serializer = self.get_serializer(instance=product)
        serializer.update(product, request.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(operation_summary="Delete a product", tags=["products"])
    def delete(self, request, pk):
        product = self.get_object()
        product.delete()
        return Response(
            {"success": "Product deleted"}, status=status.HTTP_204_NO_CONTENT
        )


class ProductCartView(APIView):
    """
    View for adding, updating or removing a product from a user's cart.
    """

    queryset = Product.objects.all()
    permission_classes = [AllowAny]
    http_method_names = ["post", "delete"]

    def get_object(self, pk):
        try:
            return get_object_or_404(Product, pk=pk)
        except Product.DoesNotExist:
            raise exceptions.NotFound({"error": "Product not found."})

    @swagger_auto_schema(
        operation_summary="Add a product to cart",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["quantity"],
            properties={
                "quantity": openapi.Schema(type=openapi.TYPE_INTEGER),
                "discount_code": openapi.Schema(type=openapi.TYPE_STRING),

            },
            example={"quantity": 12, "discount_code": "BLACKFRIDAY024"},
        ),
        tags=["products"],
    )
    def post(self, request, pk):
        product = self.get_object(pk)
        user_cart = Cart(request)
        quantity = request.data.get("quantity", 1)
        discount_code = request.data.get("discount_code")

        if quantity > product.in_stock:
            return Response(
                {"error": "The quantity cannot be more than product's stock"},
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        if not discount_code:
            user_cart.add_item(product, quantity)
            return Response(
                {"success": f"{product} has been added to cart"},
                status=status.HTTP_200_OK,
            )
            
        discount = Discount.objects.for_product().filter(code=discount_code).first()
        if not discount or not discount.is_valid():
            return Response(
                {"error": "Invalid discount code or Discount offer has expired"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if product.discount and product.discount.id == discount.id:
            user_cart.add_item(product, quantity, discount=discount)
            return Response(
                {"success": f"{product} has been added to cart"},
                status=status.HTTP_200_OK,
            )
        
        return Response(
            {"error": f"Discount with code: {discount_code} does not apply to this product"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    @swagger_auto_schema(
        operation_summary="Delete a product from cart", tags=["products"]
    )
    def delete(self, request, pk):
        product = self.get_object(pk)
        user_cart = Cart(request)
        deleted = user_cart.remove_item(product)

        if deleted:
            return Response(
                {"success": f"{product} has been removed from cart."},
                status=status.HTTP_204_NO_CONTENT,
            )

        return Response(
            {"error": f"{product} is not in cart."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ProductReviewView(GenericAPIView):
    """
    Handle review actions for products.
    
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

    @swagger_auto_schema(
        operation_summary="Get all reviews for a product",
        tags=["reviews"],
    )
    def get(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        serializer = self.get_serializer(product.reviews.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Add a review for a product", tags=["reviews"]
    )
    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        customer = request.user

        if product not in customer.products_bought.all():
            return Response(
                {
                    "error": "You can't add a review for a product you didn't purchase."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save(user=request.user, product=product)
            return Response(
                {"success": "Review posted"}, status=status.HTTP_201_CREATED
            )

        return Response({"error": "Bad request"}, status=status.HTTP_400_BAD_REQUEST)


class ProductReviewInstance(GenericAPIView):
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
        """
        Checks object permissions for PUT and DELETE requests.
        """
        if request.method.lower() in ("put", "delete"):
            self.check_object_permissions(
                request, self.get_product_review(kwargs["product_id"], kwargs["review_id"])
            )
        return super().dispatch(request, *args, **kwargs)
    
    @swagger_auto_schema(operation_summary="Get a product's review", tags=["reviews"])
    def get(self, request, product_id, review_id):
        review = self.get_product_review(product_id, review_id)
        serializer = self.get_serializer(review)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Update a product's review", tags=["reviews"]
    )
    def put(self, request, product_id, review_id):
        review = self.get_product_review(product_id, review_id)
        serializer = self.get_serializer(instance=review, data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response({"error": "Bad request"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Delete a product's review", tags=["reviews"]
    )
    def delete(self, request, product_id, review_id):
        review = self.get_product_review(product_id, review_id)
        review.delete()
        return Response(
            {"success": "Review deleted"}, status=status.HTTP_204_NO_CONTENT
        )
