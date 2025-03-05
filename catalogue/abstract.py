from django.db import models
from django.core.exceptions import ValidationError


class Timestamp(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TimeBased(Timestamp):
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    class Meta:
        abstract = True

    def clean(self):
        if self.valid_from >= self.valid_to:
            raise ValidationError(
                f"Valid to {self.valid_to} cannot be earlier than valid from {self.valid_from}"
            )
        super().clean()
