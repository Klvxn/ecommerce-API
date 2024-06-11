from django.contrib import admin

from .models import Customer, Address


# Register your models here.
admin.site.register(Address)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):

    list_display = ["email", "first_name", "last_name", "is_active", "date_joined"]
    list_filter = ["is_active", "is_superuser"]
    search_fields = ["first_name", "last_name", "email"]