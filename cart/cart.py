from decimal import Decimal

from products.models import Product


class Cart:
    """
    Using Django sessions to store cart and items in the cart
    Users will be able to add, update and delete those items.
    """

    def __init__(self, request):
        self.session = request.session
        self.session.set_expiry(1200)
        cart = self.session.get("cart")
        if not cart:
            cart = self.session["cart"] = {}
        self.cart = cart

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)

        cart = self.cart.copy()
        for product in products:
            cart[str(product.id)]['product'] = str(product)

        for item in cart.values():
            item['total_price'] = Decimal(item['price']) * item['quantity']
            item['total_price'] = str(item['total_price'])
            yield item

    def __len__(self):
        return sum(items["quantity"] for items in self.cart.values())

    def add_item(self, product, quantity=None):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {"price": str(product.price), "quantity": quantity}
            return self.save()
        else:
            self.update_item(product, quantity)

    def update_item(self, product, quantity):
        product_id = str(product.id)
        if product_id in self.cart:
            self.cart[product_id]["quantity"] = quantity
            return self.save()

    def save(self):
        self.session.modified = True
        return True

    def remove_item(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            return self.save()

    def clear(self):
        del self.session["cart"]
        self.save()

    def get_total_cost(self):
        return sum(Decimal(items["price"]) * items["quantity"] for items in self.cart.values())
