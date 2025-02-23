from rest_framework import serializers

from .models import Offer, OfferCondition, Voucher


class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        exclude = ["offer"]


class OfferConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferCondition
        exclude = ["offer", "created", "updated"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {key: value for key, value in data.items() if value is not None and value != []}


class OfferSerializer(serializers.ModelSerializer):
    voucher_set = VoucherSerializer(many=True)
    conditions = OfferConditionSerializer(many=True)

    class Meta:
        model = Offer
        fields = "__all__"
