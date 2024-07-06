from django import forms

from .models import Product, ProductAttribute
from .vouchers.models import Offer, Voucher


class CustomBaseModelForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        fields = "__all__"

    @classmethod
    def set_current_user(cls, user):
        cls.current_user = user


class AttributeModelForm(CustomBaseModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if current_user:= self.current_user:
            self.fields["product"].queryset = Product.objects.filter(store__owner=current_user)

    class Meta(CustomBaseModelForm.Meta):
        model = ProductAttribute


class OfferModelForm(CustomBaseModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if current_user:= self.current_user:
            self.fields["eligible_products"].queryset = Product.objects.filter(store__owner=current_user)

    class Meta(CustomBaseModelForm.Meta):
        model = Offer


class VoucherModelForm(CustomBaseModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if current_user:= self.current_user:
            queryset_1 = self.fields["offer"].queryset
            self.fields["offer"].queryset = queryset_1.intersection(
                Offer.objects.filter(store__owner=current_user)
            )

    class Meta(CustomBaseModelForm.Meta):
        model = Voucher
