from catalogue.forms import CustomBaseModelForm
from catalogue.models import Product

from .models import Offer, Voucher


class OfferModelForm(CustomBaseModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if current_user := self.current_user:
            pass
            # self.fields["eligible_products"].queryset = Product.objects.filter(store__owner=current_user)

    class Meta(CustomBaseModelForm.Meta):
        model = Offer
        fields = "__all__"


class VoucherModelForm(CustomBaseModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if current_user := self.current_user:
            queryset_1 = self.fields["offer"].queryset
            self.fields["offer"].queryset = queryset_1.intersection(
                Offer.objects.filter(store__owner=current_user)
            )

    class Meta(CustomBaseModelForm.Meta):
        model = Voucher
