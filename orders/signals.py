from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from customers.models import PurchaseRecord

from .models import Order, OrderStatusLog


@receiver(pre_save, sender=Order)
def log_status_change(sender, instance, **kwargs):
    if instance.pk:
        old_order = Order.objects.get(pk=instance.pk)
        if old_order.status != instance.status:
            OrderStatusLog.objects.create(
                order=instance, old_status=old_order.status, new_status=instance.status
            )


@receiver(post_save, sender=Order)
def update_purchase_record(sender, instance, **kwargs):
    if instance.status == Order.OrderStatus.PAID:
        customer = instance.customer

        items = []
        for item in instance.items.all():
            customer.products_bought.add(item.variant)

            items.append(
                PurchaseRecord(
                    customer=customer,
                    order=instance,
                    product_variant=item.variant,
                    extra={"quantity": item.quantity, "purchase_price": item.unit_price},
                )
            )

        PurchaseRecord.objects.bulk_create(items)
        customer.update_purchases_count()
