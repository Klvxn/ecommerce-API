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

    def add(self, variant, quantity, offer=None):
        product_id = variant.product.id
        variant_id = variant.id
        price = variant.final_price
        shipping = variant.product.shipping_fee or 0
        item_type = "variant" if not variant.product.is_standalone else "standalone"
        attributes = (
            variant.variant_attributes if not variant.product.is_standalone else "default"
        )
        discount = self._apply_offer(variant.product, offer) if offer else None

        item_key = f"vart_{product_id}_{variant_id}"
        item = self.cart.get(
            item_key,
            {
                "product": variant.product.name,
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
            item["discount"] = discount

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

    def get_active_offers(product, customer=None):
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

    def find_best_offer(self, product):
        """
        Finds the best applicable offer for this cart item.
        Returns the offer that gives the highest discount.
        """

        # Get all active offers for the product
        active_offers = self.get_active_offers(product, customer=self.customer)

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
        original_price = self.product.price * self.quantity

        for offer in available_offers:
            # Make sure the offer is valid for this specific purchase
            is_valid, _ = offer.satisfies_conditions(
                product=self.product, customer=self.customer
            )

            if is_valid:
                discounted_price = offer.apply_discount(original_price)
                discount_amount = original_price - discounted_price
                offer_discounts.append((offer, discount_amount))

        # Sort by discount amount and get the best offer
        if offer_discounts:
            best_offer, _ = max(offer_discounts, key=lambda x: x[1])
            return best_offer

        return None

    def apply_best_offer(self, product):
        """
        Finds and applies the best available offer to this cart item.
        Updates the cart item with the applied offer and new price.
        """
        discount = {}
        best_offer = self.find_best_offer()

        if best_offer:
            if best_offer.is_free_shipping and product.shipping_fee:
                discount["discounted_shipping"] = float(0.0)
            else:
                original_price = product.base_price
                discounted_price = best_offer.apply_discount(original_price)
                discount["discounted_price"] = float(discounted_price)

            # Update offer usage statistics if needed
            # best_offer.update_total_discount(original_price - discounted_price)

            discount["applied_offer_id"] = best_offer.id
            return True, f"Applied offer: {best_offer.title}", discount

        return False, "No applicable offers found"

    def _apply_offer(self, product, offer):
        """
        Applies discount offers to a product in the cart

        Args:
            product (Product):
            offer (Offer):

        Returns:
            dict: A dictionary containing the applied discount and details of the offer
        """
        discount = {}

        if not offer.is_free_shipping:
            if offer.for_product:
                discounted_price = self._apply_product_discount(product, offer)
                discount["discounted_price"] = float(discounted_price)
            # else:
            #     discounted_total = self._apply_order_discount(offer, self.subtotal())
            #     discount["order_discount"] = float(discounted_total)

        elif offer.is_free_shipping and product.shipping_fee:
            discount["discounted_shipping"] = float(0.0)

        discount.update({"offer_id": offer.id})
        return discount

    @staticmethod
    def _apply_product_discount(product, offer):
        """
        Applies a discount to a specific product in the cart.

        Args:
            product (Product): The product to apply the discount to.
            offer (Offer): The offer object to apply.

        Returns:
            Decimal: The discounted price if the discount is valid.
        """
        return offer.apply_discount(product.base_price)

    @staticmethod
    def _apply_order_discount(offer, order_total):
        """
        Applies a discount to the total cost of items (exc. shipping) in the cart.

        Args:
            offer (Offer): The offer object to apply.
            order_total (float): The subtotal of items in the cart.

        Returns:
            Decimal: The discounted total
        """
        if not offer.is_free_shipping:
            return offer.apply_discount(order_total)

    @staticmethod
    def calculate_item_cost(item):
        """
        Calculate the total cost of a cart item, considering any discount applied.

        Args:
            item (dict): A dictionary containing the item's price, quantity, and optional discount.

        Returns:
            Decimal: The total cost of the cart item.
        """
        return (
            Decimal(item["price"]) * item["quantity"]
            if not item.get("discount")
            else Decimal(item["discount"].get("discounted_price")) * item["quantity"]
        )

    def total_shipping(self):
        try:
            return sum(
                Decimal(value.get("shipping", 0))
                if not value.get("discount").get("discounted_shipping")
                else Decimal(value["discount"].get("discounted_shipping"))
                for value in self.cart.values()
            )
        except AttributeError:
            return sum(Decimal(value.get("shipping", 0)) for value in self.cart.values())

    def subtotal(self):
        return sum(self.calculate_item_cost(item) for item in self.cart.values())

    def total(self):
        return self.subtotal() + self.total_shipping()
