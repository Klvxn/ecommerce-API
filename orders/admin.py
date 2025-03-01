from django.contrib import admin

from .models import Order, OrderItem


# Register your models here.
class OrderItemInline(admin.StackedInline):
    model = OrderItem
    raw_id_fields = ["variant"]
    min_num = 1
    readonly_fields = [
        "product",
        "variant",
        "unit_price",
        "discounted_price",
        "quantity",
        "shipping",
        "discounted_shipping",
        "applied_offer",
        "created",
        "updated",
    ]
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    list_display = ["id", "customer", "status", "created", "updated"]
    list_filter = ["status", "created", "updated"]
    readonly_fields = ["id", "customer"]
    list_per_page = 10
