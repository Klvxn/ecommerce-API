from rest_framework import serializers

from .models import Offer, OfferCondition, Voucher


class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        exclude = ["offer"]


class OfferConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferCondition
        exclude = ["offer"]


class OfferSerializer(serializers.ModelSerializer):
    voucher_set = VoucherSerializer(many=True)
    conditions = OfferConditionSerializer(many=True)

    class Meta:
        model = Offer
        fields = "__all__"
