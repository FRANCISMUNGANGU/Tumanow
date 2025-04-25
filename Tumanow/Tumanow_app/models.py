from django.db import models
from django.db.models import CASCADE
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