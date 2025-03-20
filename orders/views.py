from django.shortcuts import redirect
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiRequest,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import reverse, status
from rest_framework.generics import (
    CreateAPIView,
    GenericAPIView,
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
    get_object_or_404,
)
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Order, OrderItem
from .serializers import CheckoutSerializer, OrderItemSerializer, OrderSerializer


# Create your views here.
@extend_schema_view(
    get=extend_schema(
        summary="Get customer orders",
        parameters=[
            OpenApiParameter(
                name="search",
                description="Search through customer's orders",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            )
        ],
        responses={200: OrderSerializer(many=True)},
        tags=["orders"],
    ),
)
class OrderListView(ListAPIView, LimitOffsetPagination):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    filterset_fields = ["status"]
    
    def get_queryset(self):
        queryset = Order.active_objects.filter(customer=self.request.user)
        queryset = self.filter_queryset(queryset)
        return queryset


@extend_schema_view(
    post=extend_schema(
        summary="Create order from customer's cart items",
        request=OpenApiRequest(
            CheckoutSerializer,
            examples=[
                OpenApiExample(
                    "Valid Request",
                    value={
                        "action": "checkout",
                        "billing_address": {
                            "street_address": "123 Main St",
                            "postal_code": "12345",
                            "city": "Anytown",
                            "state": "CA",
                            "country": "Canada",
                        },
                    },
                ),
            ],
        ),
        responses={
            201: OrderSerializer,
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT, description="Error: Bad request"
            ),
        },
        tags=["checkout"],
    )
)
class CheckoutView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CheckoutSerializer

    def get_queryset(self):
        return Order.active_objects.filter(customer=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        order = self.perform_create(serializer)
        print(order, action)
        if action == "checkout":
            return redirect(reverse.reverse("payment", args=[order.id]))

        return Response(
            {"success": True, "message": "Your Order has been saved", "order": serializer.data},
            status=status.HTTP_201_CREATED,
        )

    def perform_create(self, serializer):
        return serializer.save()


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve order object by ID",
        responses={
            200: OrderSerializer,
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Error: Not found",
                examples=[
                    OpenApiExample(
                        "Not found", value={"detail": "No order matches the given query"}
                    )
                ],
            ),
        },
        tags=["orders"],
    ),
    put=extend_schema(
        summary="Update an order object with a new billing address",
        request=OrderSerializer,
        responses={
            200: OrderSerializer,
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description="Error: Bad request"),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Error: not found",
                examples=[
                    OpenApiExample(
                        "Not found", value={"detail": "No order matches the given query"}
                    )
                ],
            ),
        },
        tags=["orders"],
    ),
    delete=extend_schema(
        summary="Delete an order",
        responses={
            204: OpenApiResponse(
                response=OpenApiTypes.NONE, description="Successful, No content"
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Error: Not found",
                examples=[
                    OpenApiExample(
                        "Not found", value={"detail": "No order matches the given query"}
                    )
                ],
            ),
        },
        tags=["orders"],
    ),
)
class OrderInstanceView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    http_method_names = ["get", "put", "delete"]

    def get_queryset(self):
        return Order.active_objects.filter(customer=self.request.user)

    def update(self, request, pk):
        order = self.get_object()

        # Only pending orders can be modified
        if order.status != Order.OrderStatus.AWAITING_PAYMENT:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = OrderSerializer(instance=order, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_delete(self, request, pk):
        order = self.get_object()
        order.is_active = False
        order.save(update_fields=["is_active"])


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve an order's order item object by ID",
        responses={
            200: OrderItemSerializer,
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Error: Not found",
                examples=[
                    OpenApiExample(
                        "Not found", value={"detail": "No order matches the given query"}
                    )
                ],
            ),
        },
        tags=["orders"],
    )
)
class OrderItemView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderItemSerializer

    def get_queryset(self):
        customer_orders = Order.active_objects.filter(customer=self.request.user)
        queryset = OrderItem.active_objects.filter(order__in=customer_orders)
        return queryset

    def get_order_item(self, order_id, order_item_id):
        qs = self.get_queryset()
        return get_object_or_404(qs, id=order_item_id, order_id=order_id)

    def get(self, request, order_id, item_id):
        order_item = self.get_order_item(order_id, item_id)
        serializer = self.get_serializer(order_item)
        return Response(serializer.data, status=status.HTTP_200_OK)
