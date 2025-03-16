import logging
from decimal import Decimal as D

from django.db import models
from django.utils import dateparse, timezone

from catalogue.models import ProductVariant
from discount.models import Offer, Voucher

logger = logging.getLogger(__name__)

class Cart:
    """
    Shopping cart implementation using Django sessions.

    Manages cart items, calculates prices, applies discounts, and
    handles inventory validation.
    """

    def __init__(self, request, force_refresh=False):
        """
        Initialize shopping cart with user session data.

        Sets up cart with current user information and loads existing cart data
        from the session.

        Args:
            request: Django request object.
            force_refresh: Whether to force a refresh of cart items.
        """
        self.customer = request.user
        self.session = request.session
        
        if "cart" in self.session:
            cart_data = self.session["cart"]
            
            if "last_activity" in cart_data:
                last_activity = dateparse.parse_datetime(cart_data["last_activity"])
                inactivity_threshold = timezone.now() - timezone.timedelta(minutes=45)
                
                if last_activity < inactivity_threshold:
                    # This approach is not ideal because it won't catch cases of sessions never getting 
                    # loaded again. That's where a cron job or a scheduled task comes in.
                    self.clear()

        self.session.set_expiry(1800)

        cart_data = self.session.setdefault(
            "cart", {"cart_items": {}, "last_refreshed": timezone.now().isoformat()}
        )
        self.meta = cart_data
        self.cart_items = cart_data["cart_items"]
        
        self.refresh(force=force_refresh)

    def __iter__(self):
        for item in self.cart_items.values():
            yield item

    def __len__(self):
        return sum(items["quantity"] for items in self.cart_items.values())

    def add(self, variant, quantity):
        logger.info(f"Adding new item: {variant.product.name} to cart: x{quantity}")
        self.refresh(force=True)

        product = variant.product
        variant_id = variant.id
        price = variant.get_final_price(self.customer)
        original_price = variant.actual_price
        offer_applied = (original_price - price) > 0  # True if an offer was applied to the product
        # shipping = product.shipping or 0
        item_type = "standalone" if product.is_standalone else "variant"

        item_key = (
            f"prod_{product.id}var_dflt"
            if product.is_standalone
            else f"prod{product.id}_var{variant.sku}"
        )
        item = self.cart_items.get(
            item_key,
            {
                "product": product.name,
                "variant_id": variant_id,
                "price": str(price),
                "original_price": str(original_price),
                "quantity": 0,
                "offer_applied": offer_applied,
                "shipping": str(0),
                "type": item_type,
            },
        )
        item["quantity"] = quantity

        if offer_applied:
            offer = product.find_best_offer(self.customer)
            self._apply_active_offer(item, offer, original_price, quantity)                
                
        self.cart_items[item_key] = item
        return self.save()

    def update(self, item_key, quantity):
        """
        Updates the quantity of a cart item by overwritting the previous quantity
        with the provided quantity

        Args:
            item_key (str): key of the item to be updated
            quantity (int): the new quantity 
        """

        if item_key not in self.cart_items:
            return False

        if quantity <= 0:
            return self.remove(item_key), "Item removed from cart"

        item = self.cart_items[item_key]
        old_quantity, new_quantity = item["quantity"], quantity
        quantity_diff = new_quantity - old_quantity
        original_price = D(item["original_price"])
        
        if "active_offer" in item and quantity_diff != 0:
            
            try:
                offer = Offer.active_objects.get(id=item["active_offer"]["offer_id"])

                # Refund the previous discount amount and reapply discount using new quantity
                prev_discount_amount = item["active_offer"]["discount_amount"]
                offer.refund_discount(prev_discount_amount)
                self._apply_active_offer(item, offer, original_price, new_quantity)

            except Offer.DoesNotExist:
                # If offer no longer exists, remove it from the item
                del item["active_offer"]
                item["offer_applied"] = False

        try:
            variant = ProductVariant.objects.get(id=item["variant_id"])
            if new_quantity > variant.stock_level:
                item["quantity"] = variant.stock_level
                message = f"Quantity limited to available stock: ({variant.stock_level})"
            else:
                item["quantity"] = new_quantity
                message = f"Quantity updated: {len(self)}"

            # Update price, offer status and voucher discounts
            current_price = variant.get_final_price(self.customer)
            self._update_offer_status(item)
            self._update_item_price(item, variant, current_price)

            if hasattr(self, "applied_voucher"):
                self._apply_voucher_to_items()

            return self.save(), message

        except ProductVariant.DoesNotExist:
            self.remove(item_key)
            return False, "Item is no longer available and was removed"

        except Exception as e:
            logger.error(f"Error updating cart item: {e}")
            return False, f"Error updating quantity: {str(e)}"

    def remove(self, item_key):
        if item_key not in self.cart_items:
            return False
        
        item = self.cart_items[item_key]
        if "active_offer" in item:
            if offer_id := item["active_offer"].get("offer_id"):
                try:
                    offer = Offer.active_objects.get(id=offer_id)
                    offer.refund_discount(item["active_offer"]["discount_amount"])
                except Offer.DoesNotExist:
                    pass
            del item["active_offer"]
            
        del self.cart_items[item_key]
        return self.save()

    def save(self):
        self.meta["last_activity"] = timezone.now().isoformat()
        self.session.modified = True
        return True

    def clear(self):
        """
        Clear the cart and refund all applied discounts back to offers.
        """
        # First refund any active offers
        for item in self.cart_items.values():
            if "active_offer" in item and "discount_amount" in item["active_offer"]:
                try:
                    if offer_id := item["active_offer"].get("offer_id"):
                        offer = Offer.active_objects.get(id=offer_id)
                        discount_amount = D(item["active_offer"]["discount_amount"])
                        offer.refund_discount(discount_amount)
                        logger.info(f"Refunded discount of {discount_amount} to offer {offer.title}")
                        
                except Offer.DoesNotExist:
                    logger.warning(f"Cannot refund discount: Offer {item.get('active_offer', {}).get('offer_id')} not found")
                    
                except Exception as e:
                    logger.error(f"Error refunding discount: {str(e)}")
        
        # Clear any applied voucher
        if "applied_voucher" in self.session:
            del self.session["applied_voucher"]
            if hasattr(self, "applied_voucher"):
                delattr(self, "applied_voucher")
        
        # Then clear the cart
        if "cart" in self.session:
            del self.session["cart"]
        
        self.save()
        return True

    def apply_voucher(self, voucher_code):
        """
        Validate and register a voucher code to the cart.

        Checks if the voucher is valid for the customer and the cart items.

        Args:
            voucher_code: The voucher code to apply.
        """
        voucher_code = voucher_code.strip().upper()
        try:
            voucher = Voucher.active_objects.get(code=voucher_code)
            valid, msg = voucher.is_valid(self.customer, self.subtotal())
            if not valid:
                return False, msg

            if voucher.offer.for_product:
                has_eligible_items = False
                for item in self.cart_items.values():
                    if item["offer_applied"]:
                        continue  # skip items with active offers

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
                "offer_type": voucher.offer.offer_type,
                "discount_type": voucher.offer.discount_type,
            }
            self._apply_voucher_to_items()
            self.applied_voucher = voucher
            return self.save(), "Voucher applied successfully"

        except Voucher.DoesNotExist:
            return False, "Invalid voucher code"

        except Exception as e:
            return False, f"Error applying voucher: {str(e)}"

    def remove_voucher(self):
        if "applied_voucher" in self.session:
            delattr(self, "applied_voucher")

            for item in self.cart_items.values():
                if "voucher_offer" in item:
                    del item["voucher_offer"]

            del self.session["applied_voucher"]

            return self.save()
        return False

    def _apply_voucher_to_items(self):
        """
        Applies voucher discount to eligible items in the cart.

        For product-specific voucher offers, discount is applied to eligible items
        and items with active offers are skipped.

        If the voucher offer is for the entire order, the discount is applied to the
        subtotal of the cart.

        Note: This internal method assumes voucher validation is already complete.
        """
        if hasattr(self, "applied_voucher"):
            voucher = self.applied_voucher
            offer = voucher.offer

            if offer.for_product:
                variant_ids = [item["variant_id"] for item in self.cart_items.values()]
                variant_map = ProductVariant.objects.select_related("product").in_bulk(variant_ids)

                for item in self.cart_items.values():
                    if item["offer_applied"]:
                        continue  # skip items with active offers

                    variant = variant_map.get(item["variant_id"])
                    if offer.valid_for_product(variant.product, self.customer):
                        item["voucher_offer"] = {
                            "voucher_id": voucher.id,
                            "discount_type": offer.discount_type,
                            "discount_amount": D("0.00"),
                        }
                        self._append_discount_to_item(
                            item,
                            offer,
                            "voucher_offer",
                            original_price=item["original_price"],
                            quantity=item["quantity"],
                        )
        return
    
    def _apply_active_offer(self, item, offer, original_price, quantity):
        """
        Applies the discount of an active offer on a product to a cart item.

        Args:
            item (dict): The cart item dictionary.
            offer (Offer): The offer object.
            original_price (Decimal): The original price of the product.
            quantity (int): The quantity of the item(product) being added.
        """
        # Get the actual discount amount that can be applied
        per_unit = offer.get_discount_amount(original_price, False)
        discount_amount = per_unit * quantity

        item["active_offer"] = {
            "offer_id": offer.id,
            "discount_amount": str(discount_amount),
            "discount_type": offer.discount_type,
            "is_valid": (offer.is_active and not offer.is_expired),
        }
        self._append_discount_to_item(item, offer, "active_offer", original_price, quantity)

    def _append_discount_to_item(self, item, offer, type, original_price, quantity):
        per_unit = offer.get_discount_amount(original_price, False)
        uncapped_discount = per_unit * quantity
        capped_discount = min(uncapped_discount, offer.remaining_discount)

        if capped_discount < uncapped_discount:
            per_unit = capped_discount / quantity
            item["price"] = str(original_price - per_unit)
            item[type]["adjusted_discount_rate"] = str(per_unit)
            item[type]["is_partial"] = True
            item[type]["discount_amount"] = str(capped_discount)
            item[type]["ideal_discount"] = str(uncapped_discount)

            if offer.is_percentage_discount:
                adjusted_percentage = (per_unit / original_price) * 100
                item[type]["adjusted_percentage"] = str(round(adjusted_percentage, 2))

            elif offer.is_fixed_discount:
                adjusted_fixed = per_unit
                item[type]["adjusted_fixed"] = adjusted_fixed

            offer.update_total_discount(capped_discount)

        else:
            # Full discount can be applied
            per_unit = uncapped_discount/ quantity
            item["price"] = str(original_price - per_unit)
            item[type]["discount_amount"] = str(per_unit)
            item[type]["just_applied"] = True
            offer.update_total_discount(uncapped_discount)

    def needs_refresh(self):
        last_refresh = dateparse.parse_datetime(self.meta.get("last_refreshed"))
        if not last_refresh:
            return True
        return (timezone.now() - last_refresh).total_seconds() > 300

    def refresh(self, force=True):
        """
        Update and validate all cart items.

        Checks product availability, stock levels, and prices.
        Removes unavailable items and adjusts quantities as needed.

        Args:
            force: Whether to skip refresh cooldown check.
        """
        if not self.needs_refresh() and not force:
            return False

        if not self.cart_items:
            return False

        logger.info("Refreshing cart items")
        variant_ids = [item["variant_id"] for item in self.cart_items.values()]
        variant_map = ProductVariant.objects.select_related("product").in_bulk(variant_ids)
        changed = False

        for key, item in self.cart_items.items():
            variant = variant_map.get(item["variant_id"])

            if not variant or not variant.is_active or variant.stock_level <= 0:
                del self.cart_items[key]
                changed = True
                continue

            if item["quantity"] > variant.stock_level:
                item["quantity"] = variant.stock_level
                changed = True

            current_price = variant.get_final_price(self.customer)
            if not self._update_offer_status(item):
                continue

            changed |= self._update_item_price(item, variant, current_price)

        if changed:
            self._apply_voucher_to_items()
            self.meta["last_refreshed"] = timezone.now().isoformat()
            # send notifs to customers
            return self.save()
        return False

    def _update_item_price(self, item, variant, current_price):
        # Skip price update if offer was just applied
        if "active_offer" in item and item["active_offer"].get("just_applied"):
            item["active_offer"].pop("just_applied", None)
            return False
        
        # If the item already has a valid active offer that's maxed out,
        # we need to preserve it rather than using the variant's current price
        has_maxed_offer = False
        if item["offer_applied"] and "active_offer" in item and item["active_offer"].get("is_valid"):
            try:
                offer_id = item["active_offer"].get("offer_id")
                offer = Offer.active_objects.get(id=offer_id)
                # Check if this is a valid but maxed offer
                if offer.maxed_out:
                    # This is a valid but maxed out offer - preserve it
                    item["active_offer"]["is_maxed_out"] = True
                    has_maxed_offer = True
            except Offer.DoesNotExist:
                pass
        
        # If we found a valid maxed offer, don't update price
        if has_maxed_offer:
            return False
            
        # Otherwise proceed with normal price update
        if item["price"] == str(current_price):
            return False
        print("Updating item price: ", item["price"], current_price)
    
        item.update({
            "price": str(current_price),
            "original_price": str(variant.actual_price),
            "offer_applied": current_price < variant.actual_price,
        })
        return True

    def _update_offer_status(self, item):
        if not item["offer_applied"]:
            if "active_offer" in item:
                del item["active_offer"]
            return False
        
        if "active_offer" in item:
            exisiting_offer_id = item["active_offer"].get("offer_id")
            try:
                existing_offer = Offer.active_objects.get(id=exisiting_offer_id)

                # Condition should always be true because active_objects manager filters valid and active
                # offers by default
                if existing_offer.is_active and not existing_offer.is_expired:
                    if not item["active_offer"].get("is_valid"):
                        item["active_offer"]["is_valid"] = True
                        return True
                    return False
                
                # Offer is expired and in-active, refund the discount amount and delete offer from the item
                if discount_amount := item["active_offer"].get("discount_amount"):
                    existing_offer.refund_discount(discount_amount)
                del item["active_offer"]
                item["offer_applied"] = False
                
            except Offer.DoesNotExist:
                del item["active_offer"]
                item["offer_applied"] = False
                
            return True

        # If offer_applied is true but active_offer isn't stored, set offer_applied to false
        item["offer_applied"] = False
        return False


    def _find_applicable_offer(self):
        applicable_offers = Offer.active_objects.filter(
            conditions__condition_type="min_order_value",
            conditions__min_order_value__gt=D("0.00"),
            offer_type="order",
            requires_voucher=False,
            total_discount_offered__lt=models.F("max_discount_allowed"),
        ).distinct()
        offer_discounts = []
        for offer in applicable_offers:
            is_valid, _ = offer.satisfies_conditions(order=self, customer=self.customer)

            if is_valid:
                discount_amount = offer.get_discount_amount(self.subtotal())
                offer_discounts.append((offer, discount_amount))

        # Sort by discount amount and get the best offer
        if offer_discounts:
            best_offer, _ = max(offer_discounts, key=lambda x: x[1])
            return best_offer

    def _apply_order_offer(self):
        best_offer = self._find_applicable_offer()
        discounted = best_offer.apply_discount(self.subtotal())
        return discounted

    def total_shipping(self):
        total = 0
        for value in self.cart_items.values():
            total += D(value.get("shipping"))
        return max(total, D("0.0"))

    def subtotal(self):
        return sum(D(item["price"]) * item["quantity"] for item in self.cart_items.values())

    def get_total_voucher_discounts(self):
        """
        Calculates the total voucher discount amount.

        Handles both product-specific and order-level vouchers.
        For product vouchers: sums individual item discounts
        For order vouchers: calculates percentage or fixed amount discount
        """
        if hasattr(self, "applied_voucher") and self.applied_voucher:
            offer = self.applied_voucher.offer
            if offer.for_product:
                return sum(
                    item.get("voucher_offer", {}).get("discount_amount", 0)
                    for item in self.cart_items.values()
                )
            elif offer.for_order:
                return offer.get_discount_amount(self.subtotal())
        return 0

    def get_total_discounts(self):
        return self.get_total_voucher_discounts() +  self._apply_order_offer()

    def total(self):
        shipping = self.total_shipping()
        subtotal = self.subtotal()
        total_discount = self.get_total_discounts()
        return subtotal + shipping - total_discount
