from decimal import Decimal

from discount.models import OfferCondition


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
        # self.session.set_expiry(1800)
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
        _, discount = self.apply_best_offer(product, quantity)

        item_key = f"VART_{product.id}_{variant.sku}"
        item = self.cart.get(
            item_key,
            {
                "product": product.name,
                # "product_id": product_id,
                "variant_id": variant_id,
                "price": float(price),
                "quantity": 0,
                "shipping": float(shipping),
                "type": item_type,
                "attributes": attributes,
            },
        )
        item["quantity"] = quantity
        if discount:
            item["applied_offer"] = discount

        self.cart[item_key] = item
        return self.save()

    def update(self, item_key, quantity):
        self.cart[item_key]["quantity"] = quantity
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

        Args:
            customer: Optional customer object to check customer-specific eligibility

        Returns:
            dict: Dictionary containing categorized offers and their details
        """
        # Get product-level offers

        product_conditions = OfferCondition.objects.filter(
            condition_type="specific_products",
            eligible_products=product,
            offer__is_active=True,
            offer__requires_voucher=False,  # Add this if you want to exclude voucher-required offers
        ).select_related("offer")

        # Get category-level offers
        category_conditions = OfferCondition.objects.filter(
            condition_type="specific_categories",
            eligible_categories=product.category,
            offer__is_active=True,
            offer__requires_voucher=False,  # Add this if you want to exclude voucher-required offers
        ).select_related("offer")

        # Collect all unique offers
        product_offers = {cond.offer for cond in product_conditions}
        category_offers = {cond.offer for cond in category_conditions}

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
            "product_offers": sorted(
                product_offers, key=lambda x: x.discount_value, reverse=True
            ),
            "category_offers": sorted(
                category_offers, key=lambda x: x.discount_value, reverse=True
            ),
            "total_offers": len(product_offers) + len(category_offers),
        }

    def _find_best_offer(self, product):
        """
        Finds the best applicable offer for this cart item.
        Returns the offer that gives the highest discount.
        """

        # Get all active offers for the product
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

    def apply_best_offer(self, product, quantity):
        """
        Finds and applies the best available offer to this cart item.
        Updates the cart item with the applied offer and new price.
        """
        discount = {}
        best_offer = self._find_best_offer(product)

        if best_offer:
            discount["offer_id"] = best_offer.id

            if best_offer.is_free_shipping and product.shipping_fee:
                discount["discounted_shipping"] = float(0.0)
            else:
                original_price = product.base_price
                discounted_price = best_offer.apply_discount(original_price)
                discount["discounted_price"] = float(discounted_price)

            # Update offer usage statistics if needed
            saved = float(original_price - discounted_price) * quantity
            best_offer.update_total_discount(saved)

            discount["discount_type"] = best_offer.discount_type
            discount["discount_value"] = float(best_offer.discount_value)
            discount["saved"] = saved
            return True, discount

        return False, "No applicable offers found"

    @staticmethod
    def item_price(item):
        return (
            Decimal(item["price"]) * item["quantity"]
            if not item.get("applied_offer")
            else Decimal(item["applied_offer"].get("discounted_price")) * item["quantity"]
        )

    def total_shipping(self):
        try:
            return sum(
                Decimal(value.get("shipping", 0))
                if not value.get("applied_offer").get("discounted_shipping")
                else Decimal(value["applied_offer"].get("discounted_shipping"))
                for value in self.cart.values()
            )
        except AttributeError:
            return sum(Decimal(value.get("shipping", 0)) for value in self.cart.values())

    def subtotal(self):
        return sum(self.item_price(item) for item in self.cart.values())

    def total(self):
        return self.subtotal() + self.total_shipping()
