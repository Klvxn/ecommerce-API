from django.db.models.signals import post_save
from django.dispatch import receiver

from catalogue.models import Product, ProductVariant


@receiver(post_save, sender=Product)
def create_default_variant(sender, instance, created, **kwargs):
    """
    When a standalone product is created, create a default variant.
    """
    if created:
        if instance.is_standalone:
            default_sku = f"PRODVAR_{instance.id}_DFLT"

            ProductVariant.objects.update_or_create(
                product=instance,
                is_default=True,
                defaults={
                    "sku": default_sku,
                    "price_adjustment": 0,
                    "stock_level": instance.total_stock_level,
                    "is_active": True,
                },
            )

            ProductVariant.objects.filter(product=instance, is_default=False).delete()
            instance.update_stock_status()

        else:
            ProductVariant.objects.filter(product=instance, is_default=True).delete()
