import json
from datetime import datetime, timezone

from django.shortcuts import redirect
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import exceptions, status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from cart.cart import Cart
from .models import Product, Review
from .serializers import (
    ProductInstanceSerializer,
    ProductReviewSerializer,
    ProductsListSerializer, AddToCartSerializer,
)
from .vouchers.models import Voucher, Offer



# Create your views here.
class ProductsListView(GenericAPIView, LimitOffsetPagination):
    """
    View to list products with filtering, searching, and pagination.
    """
    permission_classes = [AllowAny]
    serializer_class = ProductsListSerializer
    filterset_fields = ["category", "available", "store"]
    search_fields = ["name", "category__name", "label", "store__brand_name"]

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
        tags=["Product"],
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


class ProductInstanceView(GenericAPIView):
    """
    Includes method to retrieve a single product.
    """
    http_method_names = ["get"]
    queryset = Product.objects.all()
    permission_classes = [AllowAny]
    serializer_class = ProductInstanceSerializer

    @swagger_auto_schema(
        operation_summary="Retrieve a product",
        responses={200: ProductInstanceSerializer(), 404: "Not Found"},
        tags=["Product"]
    )
    def get(self, request, pk):
        product = self.get_object()
        serializer = self.get_serializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductCartView(GenericAPIView):
    """
    View for adding a product to a customer's cart.
    """

    queryset = Product.objects.all()
    permission_classes = [AllowAny]
    http_method_names = ["post"]
    serializer_class = AddToCartSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["product_id"] = self.kwargs["pk"]
        return context

    def get_applicable_offers(self, offers, customer, order_value):
        """
        Determines the best applicable offer on a product based on the order value

        Args:
            offers (Queryset): A queryset of offers on a product
            customer (Customer): The customer making the order
            order_value (Decimal): The total value of the order

        Returns:
            Offer or str: The best applicable offer or "Not authenticated" if the customer
            requires log in.
        """

        for offer in offers.filter(min_order_value__lte=order_value):
            if offer.to_all_customers:
                return offer
            if offer.to_first_time_buyers:
                if not customer.is_authenticated:
                    return "Not authenticated"
                elif customer.is_first_time_buyer():
                    return offer
        return None


    @swagger_auto_schema(
        operation_summary="Add a product to cart",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["quantity", "attribute_values"],
            properties={
                "quantity": openapi.Schema(type=openapi.TYPE_INTEGER),
                "discount_code": openapi.Schema(type=openapi.TYPE_STRING),
                "attribute_values": openapi.Schema(type=openapi.TYPE_OBJECT),
            },
            example={
                "quantity": 12,
                "discount_code": "BLACKFRIDAY024",
                "attribute_values": {
                    "size": "XL",
                    "colour": "Green",
                }
            },
        ),
        tags=["Product"],
    )
    def post(self, request, pk):
        user_cart = Cart(request)
        product = get_object_or_404(self.queryset, pk=pk)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity = serializer.validated_data["quantity"]
        selected_attrs = serializer.validated_data["attribute_values"]
        discount_code = serializer.validated_data.get("discount_code")

        # Offers available and valid for the product
        product_offers = Offer.objects.filter(
            eligible_products=product,
            valid_from__lte=datetime.now(timezone.utc),
            valid_to__gte=datetime.now(timezone.utc)
        )
        order_value = product.price * quantity

        # Process the cart without discount code
        if not discount_code:

            # Get an offer that does not require a voucher code but open to customers
            open_offer = self.get_applicable_offers(product_offers.filter(
                available_to__in=["All customers", "First time buyers"]
            ), request.user, order_value)

            if open_offer == "Not authenticated":
                return redirect(f"/auth/login/?next={self.request.path}")

            (user_cart.add_item(product, quantity, open_offer, attrs=selected_attrs)
             if open_offer
             else user_cart.add_item(product, quantity, attrs=selected_attrs))

            return Response(
                {"success": f"{product} has been added to cart"}, status=status.HTTP_200_OK,
            )

        # With discount code
        voucher = Voucher.objects.filter(code=discount_code).first()
        if voucher.offer not in product_offers:
            return Response(
                {"error": "In-applicable voucher code"}, status=status.HTTP_400_BAD_REQUEST
            )

        is_valid, _msg = voucher.is_valid(request.user, order_value)
        if not is_valid:
            return Response({"error": _msg}, status=status.HTTP_400_BAD_REQUEST)

        user_cart.add_item(product, quantity, offer=voucher.offer, attrs=selected_attrs)
        return Response(
            {"success": f"{product} has been added to cart"},
            status=status.HTTP_200_OK,
        )


class ProductReviewView(GenericAPIView):
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

    @swagger_auto_schema(
        operation_summary="Get all reviews for a product",
        responses={200: ProductReviewSerializer(many=True)},
        tags=["Review"],
    )
    def get(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        serializer = self.get_serializer(product.reviews.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Add a review for a product",
        responses={201: ProductReviewSerializer(), 400: "Bad Request"},
        tags=["Review"]
    )
    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        customer = request.user

        # only customers who purchased a product can post a review for that product
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
        # Checks object permissions for PUT and DELETE requests.
        if request.method.lower() in ("put", "delete"):
            self.check_object_permissions(
                request, self.get_product_review(kwargs["product_id"], kwargs["review_id"])
            )
        return super().dispatch(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Get a product's review",
        responses={200: ProductReviewSerializer(), 400:"Not Found"},
        tags=["Review"]
    )
    def get(self, request, product_id, review_id):
        review = self.get_product_review(product_id, review_id)
        serializer = self.get_serializer(review)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Update a product's review",
        responses={200: ProductReviewSerializer, 400: "Bad Request", 404: "Not Found"},
        tags=["Review"]
    )
    def put(self, request, product_id, review_id):
        review = self.get_product_review(product_id, review_id)
        serializer = self.get_serializer(instance=review, data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response({"error": "Bad request"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(operation_summary="Delete a product's review", tags=["Review"])
    def delete(self, request, product_id, review_id):
        review = self.get_product_review(product_id, review_id)
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
