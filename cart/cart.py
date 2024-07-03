import hashlib
from decimal import Decimal


class Cart:
    """
    A shopping cart to manage products added by a user, utilizing Django sessions.

    Attributes:
        session (SessionBase): The current Django session.
        cart (dict): A dictionary representing the cart, where product IDs are keys and
        the associated data is the value.
    """

    def __init__(self, request):
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

    def generate_item_id(self, product, attrs):
        to_hash = f"{product.id}_{product.name}_{attrs}"
        hash = hashlib.sha1(to_hash.encode()).hexdigest()
        return f"{product.id}_{hash[-10:]}"

    def add_item(self, product, quantity, offer=None, attrs=None):
        """
        Adds a product to the cart or updates its quantity if it already exists. Applies a discount if provided.

        Args:
            product (Product): The product to add or update.
            quantity (int): The quantity of the product.
            offer (Offer, optional): The offer object to apply. Defaults to None.
            attrs: (dict)

        Returns:
            bool: True if the cart was successfully saved.
        """
        _item_id = self.generate_item_id(product, attrs)

        item = self.cart.get(_item_id, {
            "product": product.name,
            "price": str(product.price),
            "quantity": 0,
            "shipping": str(product.shipping_fee) if product.shipping_fee else 0,
        })
        item["quantity"] = quantity
        item["selected_attrs"] = attrs
        if offer:
            item["discount"] = self.apply_offer(product, offer)
        self.cart[_item_id] = item
        return self.save()

    def apply_offer(self, product, offer):
        """
        Applies discount and offers to a product in the cart

        Args:
            product (Product):
            offer (Offer):

        Returns:
            dict: A dictionary containing the applied discount and details of the offer
        """
        discount = {}
        if offer.for_product:
            discounted_price = self._apply_product_discount(product, offer)
            discount["discounted_price"] = str(discounted_price)
        elif offer.for_shipping and product.shipping_fee:
            discounted_shipping = self._apply_shipping_discount(product, offer)
            discount["discounted_shipping"] = str(discounted_shipping)
        discount.update({"offer_id": offer.id, "offer_type": offer.available_to})
        return discount


    def update_item(self, item_id, quantity):
        """
        Updates the quantity of a product in the cart.

        Args:
            item_id (str): The ID of the item to update.
            quantity (int): The new quantity of the product.

        Returns:
            bool: True if the cart was successfully saved.
        """
        self.cart[item_id]["quantity"] = quantity
        return self.save()

    def save(self):
        """
        Marks the session as modified to ensure the cart is saved.

        Returns:
            bool: True if the session was marked as modified.
        """
        self.session.modified = True
        return True

    def remove_item(self, item_id):
        """
        Removes a product from the cart.

        Args:
            item_id (str): The ID of the item to remove.

        Returns:
            bool: True if the cart was successfully saved.
        """
        if item_id not in self.cart:
            return False
        del self.cart[item_id]
        return self.save()

    def clear(self):
        """
        Clears all items from the cart.

        Returns:
            None
        """
        del self.session["cart"]
        self.save()

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
        product_price = product.price
        return offer.apply_discount(product_price)

    @staticmethod
    def _apply_shipping_discount(product, offer):
        """
        Applies a discount to shipping fee of a product in the cart.

        Args:
            product (Product): The product to apply the discount to.
            offer (Offer): The offer object to apply.

        Returns:
            Decimal: The discounted shipping fee if the discount is valid.
        """
        product_shipping = product.shipping_fee
        return offer.apply_discount(product_shipping)

    @staticmethod
    def calculate_item_cost(item):
        return (
            Decimal(item["price"]) * item["quantity"]
            if not item.get("discounted_price")
            else Decimal(item["discounted_price"]) * item["quantity"]
        )

    def total_shipping_fee(self):
        """
        Calculates the total shipping fee for all items in the cart.

        Returns:
            Decimal: The total shipping fee.
        """
        amount = []
        discounted_shipping = 0
        for item in self.cart.values():
            if discount := item.get("discount"):
                discounted_shipping = discount.get("discounted_shipping", Decimal(0))
            shipping = item.get("shipping", 0)
            (amount.append(discounted_shipping)
                if discounted_shipping
                else amount.append(shipping))
        return sum(amount)

    def subtotal(self):
        """
        Calculates the cost of all items in the cart, excluding shipping.

        Returns:
            Decimal: The total cost.
        """
        return sum(self.calculate_item_cost(item)
                         for item in self.cart.values())


    def total_cost(self):
        """
        Calculates the total cost of all items in the cart, including shipping.

        Returns:
            Decimal: The total cost.
        """
        return self.subtotal() + self.total_shipping_fee()
