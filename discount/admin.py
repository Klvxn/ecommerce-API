from django.contrib import admin

from .forms import OfferModelForm, VoucherModelForm
from .models import Offer, OfferCondition, RedeemedVoucher, Voucher


# Register your models here.
class OfferConditionInline(admin.StackedInline):
    model = OfferCondition
    fk_name = "offer"
    extra = 1
    filter_horizontal = ("eligible_products", "eligible_categories")


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ["__str__", "store", "discount_type", "has_expired"]
    readonly_fields = ["store"]
    inlines = [OfferConditionInline]
    form = OfferModelForm

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(store__owner=request.user)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        form.set_current_user(request.user)
        return form


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    form = VoucherModelForm
    list_display = ["__str__", "code", "offer", "usage_type", "num_of_usage"]
    readonly_fields = ["num_of_usage"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(offer__store__owner=request.user)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        form.set_current_user(request.user)
        return form


@admin.register(RedeemedVoucher)
class RedeemedVoucherAdmin(admin.ModelAdmin):
    list_display = ["voucher", "customer", "date_redeemed"]
    readonly_fields = list_display

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(voucher__offer__store__owner=request.user)
