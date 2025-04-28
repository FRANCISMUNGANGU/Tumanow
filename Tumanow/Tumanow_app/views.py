from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login as auth_login
from .models import Restaurant, Product
from .forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse  # Import HttpResponse
from django_daraja.mpesa.core import MpesaClient  # Import MpesaClient

# Create your views here.
def home(request):
    return render(request, "index.html")

@login_required(login_url="login")
def profile(request):
    customer = request.user.customer
    return render(request, 'home.html', {'customer': customer})


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    else:
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
        phone_number = request.POST.get('phone')

        if not phone_number or not phone_number.isdigit():
            return HttpResponse('invalid phone number')

        cl = MpesaClient()
        account_reference = 'Tumanow'
        transaction_desc = 'paying for food'
        callback_url = 'https://127.0.0.1:8000/mpesa-callback/'  # You need to create this endpoint!

        # Initiate STK Push
        response = cl.stk_push(str(phone_number), amount, account_reference, transaction_desc, callback_url)

        # You need to save some transaction data like CheckoutRequestID somewhere!
        checkout_request_id = response.json()
        print(checkout_request_id) # depends how your MpesaClient returns it

        # Store it in session or database to track later
        request.session['checkout_request_id'] = checkout_request_id

        return render(request, 'processing.html', {'food': food})
    else:
        return render(request, 'checkout.html', {'food': food})

    
def check_payment_status(request):
    checkout_request_id = request.session.get('checkout_request_id')

    if not checkout_request_id:
        return JsonResponse({'status': 'error', 'message': 'No transaction found'})

    cl = MpesaClient()
    result = cl.query_transaction_status(checkout_request_id)

    # You'll need to adjust according to M-Pesa response format
    if result.get('ResultCode') == 0:
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'pending'})