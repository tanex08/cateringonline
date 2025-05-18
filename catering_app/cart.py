from decimal import Decimal
from django.conf import settings
from .models import MenuItem

class Cart:
    def __init__(self, request):
        """
        Initialize the cart.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # Save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, item, quantity=1, update_quantity=False):
        """
        Add a product to the cart or update its quantity.
        """
        item_id = str(item.id)
        if item_id not in self.cart:
            self.cart[item_id] = {'quantity': 0, 'price': str(item.price)}
        
        if update_quantity:
            self.cart[item_id]['quantity'] = quantity
        else:
            self.cart[item_id]['quantity'] += quantity
        
        if self.cart[item_id]['quantity'] <= 0:
            self.remove(item)
        else:
            self.save()

    def save(self):
        # Mark the session as "modified" to make sure it gets saved
        self.session.modified = True

    def remove(self, item):
        """
        Remove a product from the cart.
        """
        item_id = str(item.id)
        if item_id in self.cart:
            del self.cart[item_id]
            self.save()

    def __iter__(self):
        """
        Iterate over the items in the cart and get the products
        from the database.
        """
        item_ids = self.cart.keys()
        # Get the product objects and add them to the cart
        items = MenuItem.objects.filter(id__in=item_ids)
        
        cart = self.cart.copy()
        for item_obj in items:
            cart[str(item_obj.id)]['item'] = item_obj
            
        for item_data in cart.values():
            item_data['price'] = Decimal(item_data['price'])
            item_data['total_price'] = item_data['price'] * item_data['quantity']
            yield item_data

    def __len__(self):
        """
        Count all items in the cart.
        """
        return sum(item_data['quantity'] for item_data in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item_data['price']) * item_data['quantity'] for item_data in self.cart.values())

    def clear(self):
        # Remove cart from session
        del self.session[settings.CART_SESSION_ID]
        self.save() 