from django.db import models

from catalogue.models import Timestamp


# Create your models here.
class Transaction(Timestamp):
    TRANSACTION_STATUS = [
        ("successful", "Successful"),
        ("failed", "Failed"),
        ("pending", "Pending"),
        ("refunded", "Refunded"),
    ]

    order = models.OneToOneField("orders.Order", on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=255, blank=True, unique=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE)
    date_paid = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="pending", choices=TRANSACTION_STATUS)

    def __str__(self):
        return f"Payment for Order: {self.order}"
