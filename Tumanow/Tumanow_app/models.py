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
    vendor = models.OneToOneField(Vendor, on_delete=CASCADE)
    name = models.CharField(max_length=100)
    price = models.PositiveIntegerField()
    image = models.ImageField(upload_to='product_images/')
    restaurant = models.ForeignKey('Restaurant', on_delete=models.CASCADE, related_name='menu_items')


    def __str__(self):
        return self.name


class Restaurant(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = PhoneNumberField()
    image = models.ImageField(upload_to='restaurants', default='deliveryicons.jpg')

    def __str__(self):
        return self.name


