from django import forms

from .models import Product, Attribute, VariantAttribute


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
        if current_user := self.current_user:
            self.fields["product"].queryset = Product.objects.filter(store__owner=current_user)

    class Meta(CustomBaseModelForm.Meta):
        model = Attribute


class VariantAttributeInlineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.variant_id:
            # Filter attributes to only show those belonging to the product
            print("testing 1")
            product = self.instance.variant.product
            self.fields["attribute"].queryset = Attribute.objects.all()
        elif "request" in kwargs.get("initial", {}):
            # For new variants, try to get product_id from request
            print("testing 3")
            request = kwargs["initial"]["request"]
            if "product" in request.GET:
                product_id = request.GET["product"]
                self.fields["attribute"].queryset = Attribute.objects.all()
            else:
                print("testing 2")
                self.fields["attribute"].queryset = Attribute.objects.none()

    class Meta:
        model = VariantAttribute
        fields = ["attribute", "value"]
