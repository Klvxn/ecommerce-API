from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from .models import Offer
from .serializers import OfferSerializer


# Create your views here.
@extend_schema_view(
    get=extend_schema(
        summary="Get a available offers",
        responses={200: OfferSerializer(many=True)},
        tags=["Offers"],
    )
)
class OfferView(ListAPIView):
    queryset = Offer.active_objects.all()
    serializer_class = OfferSerializer
    permission_classes = [AllowAny]
