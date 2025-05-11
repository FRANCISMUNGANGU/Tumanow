from django.db import models
from django.db.models import CASCADE, SET_NULL
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField


# Create your models here.

class Vendor(models.Model):
    user = models.OneToOneField(User, on_delete=CASCADE)
    vendor_name = models.CharField(max_length=100)
    phone_number = PhoneNumberField()
    restaurant = models.ForeignKey('Restaurant', on_delete=models.CASCADE, related_name='vendor_name')


    def __str__(self):
        return self.vendor_name


class Product(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=CASCADE)
    name = models.CharField(max_length=100)
    price = models.PositiveIntegerField()
    image = models.ImageField(upload_to='product_images/')
    restaurant = models.ForeignKey('Restaurant', on_delete=models.CASCADE, related_name='menu_items')


    def __str__(self):
        return self.name


class Restaurant(models.Model):
    CATEGORY_CHOICE = [
        ('TD', 'Traditional Dishes'),
        ('FF', 'Fast Food'),
        ('S', 'Snacks'),
        ('HB', 'Hot Beverages'),
        ('CB', 'Cold Beverages')
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = PhoneNumberField()
    image = models.ImageField(upload_to='restaurants', default='deliveryicons.jpg')
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=2, choices=CATEGORY_CHOICE)

    def __str__(self):
        return self.name


class Customer(models.Model):
    customer = models.OneToOneField(User, on_delete=CASCADE)
    name = models.CharField(max_length=150)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField()
    profile_pic = models.ImageField(upload_to='users')
    phone_number = PhoneNumberField()

    def __str__(self):
        return self.username
    
class Deliverer(models.Model):
    CHOICE = [
        ('A', 'Available'),
        ('OO', 'On Order')
    ]
    user = models.OneToOneField(User, on_delete=CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=CASCADE)
    name = models.CharField(max_length=100)
    phone_number = PhoneNumberField()
    status = models.CharField(max_length=100, choices=CHOICE)
    vendor = models.ForeignKey(Vendor, on_delete=CASCADE)

    def __str__(self):
        return self.get_status_display()

class Order(models.Model):
    CHOICES = [
        ('R', 'Received'),
        ('D', 'Dispatched'),
        ('A', 'Arrived')
    ]
    customer = models.ForeignKey(Customer, on_delete=CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=CASCADE)
    vendor = models.ForeignKey(Vendor, on_delete=CASCADE)
    product = models.ForeignKey(Product, on_delete=CASCADE)
    deliverer = models.ForeignKey(Deliverer, on_delete=SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=100, choices=CHOICES)

    def __str__(self):
        return f"Order for: {self.customer.name}"
    
class STKPushTransaction(models.Model):
    phone_number = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    checkout_request_id = models.CharField(max_length=100)
    merchant_request_id = models.CharField(max_length=100)
    mpesa_receipt_number = models.CharField(max_length=100, null=True, blank=True)
    transaction_date = models.DateTimeField(null=True, blank=True)
    result_code = models.IntegerField(null=True, blank=True)
    result_desc = models.TextField()
    status = models.CharField(max_length=20, choices=[('success', 'Success'), ('failed', 'Failed')])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.phone_number
