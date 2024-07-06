from django.contrib import admin

from .models import Order, OrderItem


# Register your models here.
class OrderItemInline(admin.StackedInline):

    model = OrderItem
    raw_id_fields = ['product']
    min_num = 1
    extra = 0

 
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    inlines = [OrderItemInline]
    list_display = ['id', 'customer', 'status', 'created', 'updated']
    list_filter = ['status', 'created', 'updated']
    readonly_fields = ['id', 'customer']
    list_per_page = 10
