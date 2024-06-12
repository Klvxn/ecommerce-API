from django.contrib import admin

from .models import Order, OrderItem


# Register your models here.
class OrderItemInline(admin.TabularInline):

    model = OrderItem
    raw_id_fields = ['product']
    extra = 0

 
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    inlines = [OrderItemInline]
    list_display = ['id', 'customer', 'created', 'updated', 'status']
    list_filter = ['status', 'created', 'updated']
    list_per_page = 10
