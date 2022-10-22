from decimal import Decimal

from products.models import Product


class Cart:
    """
    Using Django sessions to store cart and items in the cart
    Users will be able to add, update and remove those items.
    """

    def __init__(self, request):
        self.session = request.session
        self.session.set_expiry(1200)
        cart = self.session.get("cart")
        if not cart:
            cart = self.session["cart"] = {}
        self.cart = cart

    def __iter__(self):
        for item in self.cart.values():
            item["total price"] = Decimal(item["price"]) * item["quantity"]
            item["total price"] = str(item["total price"])
            yield item

    def __len__(self):
        return sum(items["quantity"] for items in self.cart.values())

    def add_item(self, product: Product, quantity: int):
        if product.id not in self.cart:
            self.cart[product.id] = {
                "product": product.name,
                "price": str(product.price),
                "quantity": quantity,
            }
            return self.save()
        else:
            self.update_item(product, quantity)

    def update_item(self, product, quantity):
        product_id = str(product.id)
        self.cart[product_id]["quantity"] = quantity
        return self.save()

    def save(self):
        self.session.modified = True
        return True

    def remove_item(self, product: Product):
        if product.id in self.cart:
            del self.cart[product.id]
            return self.save()

    def clear(self):
        del self.session["cart"]
        self.save()

    def get_total_cost(self):
        return sum(Decimal(items["price"]) * items["quantity"] for items in self.cart.values())
