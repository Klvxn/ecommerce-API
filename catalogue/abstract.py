from django.db import models
from django.core.exceptions import ValidationError


class Timestamp(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ActiveObjectsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class BaseModel(Timestamp):
    is_active = models.BooleanField(default=True)

    objects = models.Manager()
    active_objects = ActiveObjectsManager()

    class Meta:
        abstract = True


class TimeBased(BaseModel):
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
