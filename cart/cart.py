from decimal import Decimal


class Cart:
    """
    A shopping cart to manage products added by a user, utilizing Django sessions.

    Attributes:
        session (SessionBase): The current Django session.
        cart (dict): A dictionary representing the cart, where product IDs are keys and the associated data is the value.
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
            cost = self.calculate_item_cost(item)
            item["cost"] = f"${cost:.2f}"
            yield item

    def __len__(self):
        return sum(items["quantity"] for items in self.cart.values())

    def add_item(self, product, quantity, offer=None):
        """
        Adds a product to the cart or updates its quantity if it already exists. Applies a discount if provided.

        Args:
            product (Product): The product to add or update.
            quantity (int): The quantity of the product.
            offer (Offer, optional): The offer object to apply. Defaults to None.

        Returns:
            bool: True if the cart was successfully saved.
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                "product": product.name,
                "price": str(product.price),
                "quantity": quantity,
                "discounted_price": None,
                "shipping": str(product.shipping_fee) if product.shipping_fee else None,
            }
        else:
            self.update_item(product, quantity)
        if offer is not None:
            if offer.for_product:
                discounted_price = self._apply_product_discount(product, offer)
                self.cart[product_id]["discounted_price"] = str(discounted_price)
            elif offer.for_shipping and product.shipping_fee:
                discounted_shipping = self._apply_shipping_discount(product, offer)
                self.cart[product_id]["shipping"] = str(discounted_shipping)
        return self.save()

    def update_item(self, product, quantity):
        """
        Updates the quantity of a product in the cart.

        Args:
            product (Product): The product to update.
            quantity (int): The new quantity of the product.

        Returns:
            bool: True if the cart was successfully saved.
        """
        product_id = str(product.id)
        self.cart[product_id]["quantity"] = quantity
        return self.save()

    def save(self):
        """
        Marks the session as modified to ensure the cart is saved.

        Returns:
            bool: True if the session was marked as modified.
        """
        self.session.modified = True
        return True

    def remove_item(self, product):
        """
        Removes a product from the cart.

        Args:
            product (Product): The product to remove.

        Returns:
            bool: True if the cart was successfully saved.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
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
            Decimal | None: The discounted price if the discount is valid and applicable, otherwise None.
        """
        product_price = product.price
        return offer.apply_discount(product_price)

    @staticmethod
    def _apply_shipping_discount(product, offer):
        product_shipping = product.shipping_fee
        return offer.apply_discount(product_shipping)

    @staticmethod
    def calculate_item_cost(item):
        return (
            Decimal(item["price"]) * item["quantity"]
            if not item["discounted_price"]
            else Decimal(item["discounted_price"]) * item["quantity"]
        )

    def get_total_shipping_fee(self):
        """
        Calculates the total shipping fee for all items in the cart.

        Returns:
            Decimal: The total shipping fee.
        """
        return (
            sum(Decimal(item["shipping"])
            if item["shipping"] != "None"
            else 0
            for item in self.cart.values())
        )

    def get_total_cost(self):
        """
        Calculates the total cost of all items in the cart, including shipping.

        Returns:
            Decimal: The total cost.
        """
        total_cost = sum(self.calculate_item_cost(item) for item in self.cart.values())
        return total_cost + self.get_total_shipping_fee()
