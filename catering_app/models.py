from django.db import models
from django.conf import settings # For ForeignKey to User


class MenuCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)


    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Menu Categories"

class MenuItem(models.Model):
    category = models.ForeignKey(MenuCategory, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True) 
    is_available = models.BooleanField(default=True)
   

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('PENDING', 'Pending Confirmation'),
        ('CONFIRMED', 'Confirmed'),
        ('PREPARING', 'Preparing'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    delivery_address = models.TextField()
    scheduled_datetime = models.DateTimeField()
    number_of_guests = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='PENDING')

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'Order {self.id} by {self.user.username}'

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2) 
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity

class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)] 

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review') 
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

        unique_together = (('order', 'user'),) 

    def __str__(self):
        return f'Review for Order {self.order.id} by {self.user.username} - {self.rating} stars'
