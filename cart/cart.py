from decimal import Decimal

from catalogue.models import ProductVariant
from discount.models import Offer


class Cart:
    """
    A shopping cart to manage products added by a user, utilizing Django sessions.

    Attributes:
        session (SessionBase): The current Django session.
        cart (dict): A dictionary representing the cart, where product IDs are keys and
        the associated data is the value.
    """

    def __init__(self, request):
        self.customer = request.user
        self.session = request.session
        self.session.set_expiry(1800)
        cart = self.session.get("cart")
        if not cart:
            cart = self.session["cart"] = {}
        self.cart = cart

    def __iter__(self):
        for item in self.cart.values():
            yield item

    def __len__(self):
        return sum(items["quantity"] for items in self.cart.values())

    def add(self, variant, quantity):
        product = variant.product
        variant_id = variant.id
        price = variant.final_price
        shipping = product.shipping_fee or 0
        item_type = "standalone" if product.is_standalone else "variant"
        attributes = "default" if product.is_standalone else variant.attributes
        offer_applied, discount = self.apply_best_offer(variant, quantity)

        item_key = f"prod{product.id}_{variant.sku}_dflt"
        item = self.cart.get(
            item_key,
            {
                "product": product.name,
                "variant_id": variant_id,
                "price": float(price),
                "quantity": 0,
                "shipping": float(shipping),
                "type": item_type,
                "attributes": attributes,
            },
        )
        item["quantity"] = quantity
        if offer_applied:
            item["applied_offer"] = discount

        self.cart[item_key] = item
        return self.save()

    def update(self, item_key, quantity):
        item = self.cart[item_key]
        item["quantity"] += quantity
        variant = ProductVariant.objects.get(id=item["variant_id"])
        applied, offer = self.apply_best_offer(variant, quantity)
        if applied:
             item["applied_offer"] = offer
        else:
            item.pop("applied_offer", None)
        return self.save()

    def remove(self, item_key):
        if item_key not in self.cart:
            return False
        del self.cart[item_key]
        return self.save()

    def save(self):
        self.session.modified = True
        return True

    def clear(self):
        del self.session["cart"]
        self.save()

    def _get_active_offers(self, product, customer=None):
        """
        Get all active offers applicable to this product, either directly or through its category.
        Groups offers by type (product-specific, category-wide) and excludes expired offers.
        """
        # Get product-level offers
        product_offers = Offer.objects.filter(
            target="Product",
            requires_voucher=False,
            conditions__condition_type="specific_products",
            conditions__eligible_products=product,
        ).distinct()

        # Get category-level offers
        category_offers = Offer.objects.filter(
            target="Product",
            conditions__condition_type="specific_categories",
            conditions__eligible_categories=product.category,
            requires_voucher=False, 
        ).distinct()

        # If customer is provided, filter out offers they're not eligible for
        if customer:
            product_offers = {
                offer
                for offer in product_offers
                if offer.satisfies_conditions(product=product, customer=customer)[0]
            }
            category_offers = {
                offer
                for offer in category_offers
                if offer.satisfies_conditions(product=product, customer=customer)[0]
            }

        return {
            "product_offers": sorted(product_offers, key=lambda x: x.discount_value, reverse=True),
            "category_offers": sorted(category_offers, key=lambda x: x.discount_value, reverse=True),
            "total_offers": len(product_offers) + len(category_offers)
        }

    def _get_applicable_order_offers(self):
        active_offers = Offer.objects.filter(
            target="Order",
            requires_voucher=False,
            is_active=True,
            conditions__condition_type="min_order_value",
        )
        return {offer for offer in active_offers if offer.valid_for_order(order=self)}

    def _find_best_order_offers(self):
        available_offers = list(self._get_applicable_order_offers())
        if not available_offers:
            return None
        return max(available_offers, key=lambda x: x.discount_value)
    
    def _find_best_offer(self, product):
        """
        Finds the best applicable offer for this cart item.
        Returns the offer that gives the highest discount.
        """
        active_offers = self._get_active_offers(product, customer=self.customer)

        # Combine all applicable offers
        all_offers = list(active_offers["product_offers"]) + list(
            active_offers["category_offers"]
        )

        # Filter out offers that require vouchers
        available_offers = [offer for offer in all_offers if not offer.requires_voucher]
        if not available_offers:
            return None

        # Calculate the actual discount amount for each offer
        offer_discounts = []
        original_price = product.base_price

        for offer in available_offers:
            # Make sure the offer is valid for this specific purchase
            is_valid, _ = offer.satisfies_conditions(product=product, customer=self.customer)

            if is_valid:
                discounted_price = offer.apply_discount(original_price)
                discount_amount = original_price - discounted_price
                offer_discounts.append((offer, discount_amount))

        # Sort by discount amount and get the best offer
        if offer_discounts:
            best_offer, _ = max(offer_discounts, key=lambda x: x[1])
            return best_offer

        return None

    def apply_best_offer(self, variant, quantity):
        """
        Finds and applies the best available offer to this cart item.
        Updates the cart item with the applied offer and new price.
        """
        discount = {}
        product = variant.product
        best_offer = self._find_best_offer(product)
            
        if best_offer:
            discount["offer_id"] = best_offer.id

            if best_offer.is_free_shipping and product.shipping_fee:
                discount["discounted_shipping"] = float(0.0)
            else:
                original_price = variant.final_price * quantity
                discounted_price = best_offer.apply_discount(original_price)
                discount["discounted_price"] = float(discounted_price)

            # Update offer usage statistics 
            saved = float(original_price - discounted_price)
            best_offer.update_total_discount(saved)

            discount["discount_type"] = best_offer.discount_type
            discount["discount_value"] = float(best_offer.discount_value)
            discount["saved"] = saved
            return True, discount

        return False, None

    def _get_order_offer(self):
        best_offer = self._find_best_order_offers()
        if best_offer:
            return {
                "offer_id": best_offer.id,
                "offer_title": best_offer.title,
                "discount_value": best_offer.discount_value,
                "discount_type": best_offer.discount_type,
            }
        return None

    @staticmethod
    def item_price(item):
        quantity = item["quantity"]
        offer = item.get("applied_offer")
        if offer and hasattr(offer, "discounted_price"):
            return Decimal(offer.get("discounted_price")) * quantity
        return Decimal(item["price"]) * quantity

    def total_shipping(self):
        total = 0
        for value in self.cart.values():
            applied_offer = value.get("applied_offer")
            if applied_offer and hasattr(applied_offer, "discounted_shipping"):
                total += applied_offer.get("discounted_shipping")
            else:
                total += value.get("shipping")
        return max(total, Decimal("0.0"))

    def subtotal(self):
        return sum(self.item_price(item) for item in self.cart.values())

    def total(self):
        shipping = self.total_shipping()
        subtotal = self.subtotal()
        order_offer = self._get_order_offer()
        total = 0
        if order_offer:
            try:
                offer = Offer.objects.get(id=order_offer["offer_id"], target="Order")
                if offer.is_free_shipping:
                    shipping = Decimal('0.0')
                else:
                    total = offer.apply_discount(subtotal + Decimal(shipping))
            except offer.DoesNotExist:
                pass
        return Decimal(total) if total else subtotal + Decimal(shipping) 
