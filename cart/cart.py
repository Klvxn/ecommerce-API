import logging
from decimal import Decimal as D

from django.utils import dateparse, timezone

from catalogue.models import ProductVariant
from discount.models import Voucher

logger = logging.getLogger(__name__)

class Cart:
    """
    A shopping cart to manage products added by a user, utilizing Django sessions.

    Attributes:
        session (SessionBase): The current Django session.
        cart (dict): A dictionary representing the cart, where product IDs are keys and
        the associated data is the value.
    """

    def __init__(self, request, force_refresh=False):
        self.customer = request.user
        self.session = request.session
        self.session.set_expiry(1800)

        cart_data = self.session.setdefault(
            "cart",
            {"cart_items": {}, "version": 0.10, "last_refreshed": timezone.now().isoformat()},
        )
        self.meta = self.cart = cart_data
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
        offer_applied = (original_price - price) > 0  # determines if an offer was appplied automatically to the product
        # shipping = product.shipping or 0
        item_type = "standalone" if product.is_standalone else "variant"

        item_key = f"prod{product.id}_{variant.sku}_dflt"
        item = self.cart_items.get(
            item_key,
            {
                "product": product.name,
                "variant_id": variant_id,
                "price": float(price),
                "original_price": float(original_price),
                "quantity": 0,
                "offer_applied": offer_applied,
                "shipping": float(0),
                "type": item_type,
            },
        )
        item["quantity"] = quantity

        if offer_applied:
            offer = product.find_best_offer(self.customer)
            item["active_offer"] = {
                "offer_id": offer.id,
                "requires_voucher": offer.requires_voucher,
                "is_valid": (offer.is_active and not offer.is_expired),
            }

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
                "target": voucher.offer.target,
                "discount_type": voucher.offer.discount_type,
            }
            self._apply_voucher_discount_to_items()
            self.applied_voucher = voucher
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
        if hasattr(self, "applied_vouched"):
            voucher = self.applied_voucher
            offer = voucher.offer

            if offer.for_product:
                variant_ids = [item["variant_id"] for item in self.cart_items.values()]
                variants = ProductVariant.objects.select_related("product").filter(id__in=variant_ids)
                variant_map = {variant.id: variant for variant in variants}

                for item in self.cart_items.values():
                    if item["offer_applied"]:
                        continue  # skip items with active offers

                    variant = variant_map.get(item["variant_id"])
                    if offer.valid_for_product(variant.product, self.customer):
                        item_price = item["price"] * item["quantity"]
                        if offer.is_percentage_discount:
                            discount_amount = item_price * D(offer.discount_value / 100)
                        elif offer.is_fixed_discount:
                            discount_amount = min(offer.discount_value, item_price)

                        discount_amount = round(discount_amount, 2)
                        item["voucher_discount"] = {
                            "voucher_id": voucher.id,
                            "discount_type": offer.discount_type,
                            "discount_amount": discount_amount,
                        }
            self.save()
        return

    def needs_refresh(self):
        last_refresh = dateparse.parse_datetime(self.meta.get("last_refreshed"))
        if not last_refresh:
            return True
        return (timezone.now() - last_refresh).total_seconds() > 300

    def refresh(self, force=True):
        if not self.needs_refresh() and not force:
            return False
       
        logger.info("Refreshing cart items")        
        variant_ids = [item["variant_id"] for item in self.cart_items.values()]
        variants = ProductVariant.objects.select_related("product").filter(id__in=variant_ids)
        variant_map = {variant.id: variant for variant in variants}
        changed = False

        for key, item in self.cart_items.items():
            variant = variant_map.get(item["variant_id"])

            if not variant or not variant.is_active:
                del self.cart_items[key]
                changed = True
                continue

            current_price = variant.get_final_price(self.customer)
            if not self._update_item_price(item, variant, current_price):
                continue

            changed |= self._update_offer_status(item, variant)

        if changed:
            self._apply_voucher_discount_to_items()
            self.meta["last_refreshed"] = timezone.now().isoformat()
            self.meta["version"] = round(self.meta["version"] + 0.1, 2)
            # send notifs to customers
            return self.save()
        return False

    def _update_item_price(self, item, variant, current_price):
        if item["price"] == float(current_price):
            return False

        item.update({
            "price": float(current_price),
            "original_price": float(variant.actual_price),
            "offer_applied": current_price < variant.actual_price,
        })
        return True

    def _update_offer_status(self, item, variant):
        if not item["offer_applied"]:
            if "active_offer" in item:
                del item["active_offer"]
            return False

        try:
            offer = variant.product.find_best_offer(self.customer)
            is_valid = offer and offer.is_active and not offer.is_expired
            if "active_offer" not in item:
                item["active_offer"] = {
                    "offer_id": offer.id if offer else None,
                    "requires_voucher": offer.requires_voucher if offer else None,
                    "is_valid": is_valid,
                }
                return True
        except AttributeError:
            is_valid = False

        if is_valid == item["active_offer"]["is_valid"]:
            return False

        item["active_offer"]["is_valid"] = is_valid
        return True

    def total_shipping(self):
        total = 0
        for value in self.cart_items.values():
            total += value.get("shipping")
        return max(total, D("0.0"))

    def subtotal(self):
        return sum(item["price"] * item["quantity"] for item in self.cart_items.values())

    def get_total_voucher_discounts(self):
        if hasattr(self, "applied_vouched"):
            offer = self.applied_voucher.offer
            if offer.for_product:
                return sum(
                    item.get("voucher_discount", {}).get("discount_amount", 0)
                    for item in self.cart_items.values()
                )
            elif offer.for_order:
                if offer.is_percentage_discount:
                    return round(self.subtotal() * (offer.discount_value) / 100)
                elif offer.is_fixed_discount:
                    return min(offer.discount_value, self.subtotal())
        return 0

    def total(self):
        shipping = self.total_shipping()
        subtotal = self.subtotal()
        total_discount = self.get_total_voucher_discounts()
        return subtotal + shipping - total_discount
