from django.shortcuts import render, get_object_or_404, redirect
from .models import Restaurant, Product, Customer
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login, authenticate
from .utils import clean_input, validate_signup_data
from django_daraja.mpesa.core import MpesaClient
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse


# Create your views here.
def home(request):
    return render(request, "index.html")

@login_required(login_url="login")
def profile(request):
    customer = request.user.customer
    return render(request, 'home.html', {'customer': customer})


def register(request):
    if request.method == 'POST':
        data = {
            'name': clean_input(request.POST.get('name')),
            'username': clean_input(request.POST.get('username')),
            'email': clean_input(request.POST.get('email')).lower(),
            'phone_number': clean_input(request.POST.get('phone_number')),
            'password': request.POST.get('password', ''),
            'confirm_password': request.POST.get('confirm-password', ''),
            'profile_pic': request.FILES.get('profile_pic')
        }

        is_valid, error_msg = validate_signup_data(data)
        if not is_valid:
            messages.error(request, error_msg)
            return redirect('register')

        if User.objects.filter(username=data['username']).exists():
            messages.error(request, "Username already taken.")
            return redirect('register')

        if User.objects.filter(email=data['email']).exists():
            messages.error(request, "Email already in use.")
            return redirect('login')

        user = User.objects.create_user(username=data['username'], email=data['email'], password=data['password'])

        Customer.objects.create(
            customer=user,
            name=data['name'],
            username=data['username'],
            email=data['email'],
            phone_number=data['phone_number'],
            profile_pic=data['profile_pic']
        )

        login(request, user)
        messages.success(request, "Account created successfully!")
        return redirect('home')

    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password")
            return redirect('login')

    return render(request, 'login.html')

def menu(request):
    products = Product.objects.all()
    return render(request, 'menu.html', {'products': products})

@login_required(login_url="login")
def checkout(request, id):
    food = get_object_or_404(Product, pk=id)
    return render(request, 'checkout.html', {'food':food})

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

def process_checkout(request, id):
    food = get_object_or_404(Product, pk=id)
    if request.method == 'POST':
        amount = food.price
        phoneNumber = request.POST.get('phone')
        if not phoneNumber or not int(phoneNumber):
            return HttpResponse('invalid phone number')
        if not amount or not int(amount):
            return HttpResponse('invalid price')
        cl = MpesaClient()
        phone_number = int(phoneNumber)
        amount = int(amount)
        account_reference = 'Tumanow'
        transaction_desc = 'paying for food'
        callback_url = 'https://api.darajambili.com/express-payment'
        response = cl.stk_push(str(phone_number), amount, account_reference, transaction_desc, callback_url)
        return HttpResponse(response)
    else:
        return render(request, 'checkout.html', {'food':food})