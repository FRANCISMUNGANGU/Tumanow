from django.shortcuts import render, get_object_or_404
from .models import Restaurant, Product

# Create your views here.
def home(request):
    return render(request, "index.html")

def register(request):
    return render(request, 'register.html')

def login(request):
    return render(request, 'login.html')

def menu(request):
    products = Product.objects.all()
    return render(request, 'menu.html', {'products': products})

def checkout(request):
    return render(request, 'checkout.html')

def restaurants(request):
    restaurants = Restaurant.objects.all()
    return render(request, 'restaurants.html', {'restaurants': restaurants})

def product(request, id):
    return render(request, 'product.html')

def restaurant(request, id):
    restaurant = get_object_or_404(Restaurant, pk=id)
    menus = restaurant.menu_items.all()
    context = {
        'restaurant': restaurant, 
        'menus': menus,
    }
    return render(request, 'restaurant.html', context)
