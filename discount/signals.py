from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import OfferCondition


@receiver(post_save, sender=OfferCondition)
def create_offer_mappings(sender, instance, created, **kwargs):
    """
    When an OfferCondition is created or updated, create the appropriate mappings.
    """
    if instance.condition_type == "specific_products":
        # Create product mappings
        instance.offer.assign_to_products(instance.eligible_products.all())

    elif instance.condition_type == "specific_categories":
        # Create category mappings
        instance.offer.assign_to_categories(instance.eligible_categories.all())


@receiver(post_delete, sender=OfferCondition)
def remove_offer_mappings(sender, instance, **kwargs):
    """
    When an OfferCondition is deleted, remove the appropriate mappings.
    """
    if instance.condition_type == "specific_products":
        instance.offer.remove_from_products(instance.eligible_products.all())

    elif instance.condition_type == "specific_categories":
        instance.offer.remove_from_categories(instance.eligible_categories.all())
