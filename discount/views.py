from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny


from .models import Offer
from .serializers import OfferSerializer


# Create your views here.
class OfferView(ListAPIView):
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    permission_classes = [AllowAny]
