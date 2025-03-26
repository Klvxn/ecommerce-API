from django import forms


class CustomBaseModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        fields = "__all__"

    @classmethod
    def set_current_user(cls, user):
        cls.current_user = user
