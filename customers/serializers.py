from django.contrib.auth.password_validation import validate_password
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from .models import Address, Customer


class AddressSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Address
        exclude = ["id"]

    def validate_country(self, data):
        if len(data) <= 3:
            raise serializers.ValidationError("Country name should be in full")
        return data


class CustomerSerializer(serializers.ModelSerializer):

    address = AddressSerializer(read_only=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, validators=[validate_password]    )

    class Meta:
        model = Customer
        fields = [
            "email",
            "first_name",
            "last_name",
            "slug",
            "date_of_birth",
            "address",
            "password",
            "password2",
        ]
        extra_kwargs = {
            "first_name": {"required": True}, "last_name": {"required": True}
        }

    def validate(self, attrs):
        pwd = attrs["password"]
        pwd2 = attrs["password2"]
        if pwd != pwd2 and pwd2:
            raise serializers.ValidationError({"error": "Passwords don't match"})
        return attrs

    def create(self, validated_data):
        data = validated_data
        data.pop("password2")
        customer = Customer.objects.create_user(
            email=data["email"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            date_of_birth=data["date_of_birth"],
            password=data["password"],
        )
        return customer


class CustomerUpdateSerializer(WritableNestedModelSerializer):

    address = AddressSerializer(required=False)

    class Meta:
        model = Customer
        fields = [
            "email",
            "first_name",
            "last_name",
            "slug",
            "date_of_birth",
            "address",
        ]


class SimpleCustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Customer
        fields = ["email", "first_name", "last_name"]
