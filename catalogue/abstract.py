from datetime import datetime, timezone

from django.core.exceptions import ValidationError
from django.db import models


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
        default_manager_name = "objects"


class ValidObjectsManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                valid_from__lte=datetime.now(timezone.utc),
                valid_to__gt=datetime.now(timezone.utc),
                is_active=True,
            )
        )


class TimeBased(BaseModel):
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    active_objects = ValidObjectsManager()

    class Meta(BaseModel.Meta):
        abstract = True

    def clean(self):
        if self.valid_from >= self.valid_to:
            raise ValidationError(
                f"Valid to {self.valid_to} cannot be earlier than valid from {self.valid_from}"
            )
        super().clean()
