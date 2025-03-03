from decimal import Decimal

from catalogue.models import ProductVariant
from discount.models import Offer, Voucher


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
            cart["cart_items"] = {}
        self.cart = cart
        self.cart_items = cart.get("cart_items")

    def __iter__(self):
        for item in self.cart_items.values():
            yield item

    def __len__(self):
        return sum(items["quantity"] for items in self.cart_items.values())

    def add(self, variant, quantity):
        product = variant.product
        variant_id = variant.id
        price = variant.final_price
        shipping = product.shipping_fee or 0
        item_type = "standalone" if product.is_standalone else "variant"
        attributes = "default" if product.is_standalone else variant.attributes

        item_key = f"prod{product.id}_{variant.sku}_dflt"
        item = self.cart_items.get(
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
        self.cart_items[item_key] = item
        return self.save()

    def update(self, item_key, quantity):
        item = self.cart_items[item_key]
        item["quantity"] += quantity
        return self.save()

    def remove(self, item_key):
        if item_key not in self.cart_items:
            return False
        del self.cart_items[item_key]
        return self.save()

    def save(self):
        self.session.modified = True
        return True

    def clear(self):
        del self.session["cart"]
        self.save()

    def apply_voucher(self, voucher_code):
        voucher_code = voucher_code.strip().upper()
        try:
            voucher = Voucher.objects.get(code=voucher_code)
            valid, msg = voucher.is_valid(self.customer, self.subtotal())
            if not valid:
                return False, msg

            if voucher.offer.for_product:
                has_eligible_items = False
                for item in self.cart_items.values():
                    variant = ProductVariant.objects.get(id=item["variant_id"])
                    if voucher.offer.valid_for_product(variant.product, self.customer):
                        has_eligible_items = True
                        break

                if not has_eligible_items:
                    return False, "No item in your cart is eligible for the voucher offer"

            self.session["applied_voucher"] = {
                "id": voucher.id,
                "code": voucher_code,
                "offer": voucher.offer.title,
                "target": voucher.offer.target,
                "discount_type": voucher.offer.discount_type,
            }
            self._apply_voucher_discount_to_items()
            self.applied_voucher = voucher.offer
            return self.save(), "Voucher applied successfully"

        except Voucher.DoesNotExist:
            return False, "Invalid voucher code"

        except Exception as e:
            return False, f"Error applying voucher: {str(e)}"

    def remove_voucher(self):
        if "applied_voucher" in self.session:
            self.applied_voucher = None
            for item in self.cart_items.values():
                if "voucher_discount" in item:
                    del item["voucher_discount"]
            del self.session["applied_voucher"]
            return self.save()
        return False

    def _apply_voucher_discount_to_items(self):
        try:
            offer = self.applied_voucher
            if offer.for_product:
                for item in self.cart_items.values():
                    variant = ProductVariant.objects.get(id=item["variant_id"])
                    if offer.valid_for_product(variant.product, self.customer):
                        item_price = item["price"] * item["quantity"]
                        if offer.is_percentage_discount:
                            discount_amount = item_price * Decimal(offer.discount_value / 100)
                        elif offer.is_fixed_discount:
                            discount_amount = min(offer.discount_value, item_price)

                        discount_amount = round(discount_amount, 2)
                        item["item_discount"] = {
                            "offer_title": offer,
                            "discount_type": offer.discount_type,
                            "discount_amount": discount_amount,
                        }
            self.save()
        except AttributeError:
            return

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
        active_offers = self._get_active_offers(product, customer=self.customer)

        # Combine all applicable offers
        available_offers = list(active_offers["product_offers"]) + list(
            active_offers["category_offers"]
        )

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
        offer_discount = {}
        product = variant.product
        best_offer = self._find_best_offer(product)

        if best_offer:
            offer_discount["offer_id"] = best_offer.id

            if best_offer.is_free_shipping and product.shipping_fee:
                offer_discount["discounted_shipping"] = float(0.0)
            else:
                original_price = variant.final_price * quantity
                discounted_price = best_offer.apply_discount(original_price)
                offer_discount["discounted_price"] = float(discounted_price)

            # Update offer usage statistics
            saved = float(original_price - discounted_price)
            best_offer.update_total_discount(saved)

            offer_discount["discount_type"] = best_offer.discount_type
            offer_discount["discount_value"] = float(best_offer.discount_value)
            offer_discount["saved"] = saved
            return True, offer_discount

        return False, None

    def total_shipping(self):
        total = 0
        for value in self.cart_items.values():
            applied_offer = value.get("applied_offer")
            if applied_offer and hasattr(applied_offer, "discounted_shipping"):
                total += applied_offer.get("discounted_shipping")
            else:
                total += value.get("shipping")
        return max(total, Decimal("0.0"))

    def subtotal(self):
        return sum(item["price"] * item["quantity"] for item in self.cart_items.values())

    def get_total_voucher_discounts(self):
        try:
            offer = self.applied_voucher
            if offer.for_product:
                return sum(
                    item.get("item_discount", {}).get("discount_amount", 0)
                    for item in self.cart_items.values()
                )
            elif offer.for_order:
                if offer.is_percentage_discount:
                    return round(self.subtotal() * (offer.discount_value) / 100)
                elif offer.is_fixed_discount:
                    return min(offer.discount_value, self.subtotal())
            else:
                return 0
        except AttributeError:
            return 0

    def total(self):
        shipping = self.total_shipping()
        subtotal = self.subtotal()
        total_discount = self.get_total_voucher_discounts()
        return subtotal + shipping - total_discount
