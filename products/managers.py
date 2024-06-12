from django.db import models
        

class DiscountQuerySet(models.QuerySet):
    """
    Manager to handle querysets specifically for order discounts.
    """
    def for_product(self):
        return self.filter(discount_type="product_discount")
    
    def for_order(self):
        return self.filter(discount_type="order_discount")
