from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login as auth_login 
from django.contrib.auth import logout as auth_logout
from .models import Restaurant, Product, STKPushTransaction, Order, Customer, Vendor
from .utils import normalize_phone, get_access_token
import requests
import json
from .forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse  
from django.contrib import messages  
from django.core.mail import send_mail  
from django.conf import settings 
from django.views.decorators.csrf import csrf_exempt  
from datetime import datetime 
import base64  

# Create your views here.


def home(request):
    """
    This view is used to render the home page
    """
    return render(request, "index.html")

@login_required(login_url="login")
def profile(request):
    """
    This view is used to render the logged user and profile pic
    """
    customer = request.user.customer
    return render(request, 'home.html', {'customer': customer})

@login_required(login_url="login")
def profile_page(request):
    """
    This view is used to render the profile that has customer order history
    """
    customer = request.user.customer
    orders = Order.objects.filter(customer=customer)
    return render(
        request, 'profile.html',
                   {'customer': customer,
                    'orders': orders
                    }
    )

@login_required(login_url='login')
def place_order(request, id):
    """
    This view is used to place an order and send an email if the order placement is successful
    to:
        1. Restaurant
        2. Vendor
        3. Customer
    """
    food = get_object_or_404(Product, pk=id)
    customer = request.user.customer
    vendor = food.vendor
    restaurant = food.restaurant
    order = Order.objects.create(
        customer = customer,
        restaurant = restaurant,
        vendor = vendor,
        product = food,
        status = 'Received'
    )
    subject= f"Order Confirmation for {food.name}"
    message_customer = f"An order has been placed for {food.name}.\n\nOrder ID: {order.id}"
    message_vendor = f"An order has been place for {food.name} by {customer.name}.\n Customer number: {customer.phone_number}\n Customer Email: {customer.email} \n Order Id: {order.id}"
    message_restaurant = f"An order has been place for {food.name} by {customer.name}.\n Customer number: {customer.phone_number}\n Customer Email: {customer.email} \n Vendor Name: {vendor.vendor_name} \n Vendor Email: {vendor.user.email} \n Vendor Phone Number: {vendor.phone_number} \n Order Id: {order.id}"
    from_email = 'mungangufrancis8@gmail.com'

    recipients = [
        customer.email,
        vendor.user.email,
        restaurant.email
    ]

    send_mail(
        subject=subject,
        message=message_customer,
        from_email=from_email,
        recipient_list=[customer.email],
        fail_silently=False,
    )

    # Message to vendor
    send_mail(
        subject='New Order Received',
        message=message_vendor,
        from_email=from_email,
        recipient_list=[vendor.user.email],
        fail_silently=False,
    )

    # Message to restaurant
    send_mail(
        subject='New Order for Your Restaurant',
        message=message_restaurant,
        from_email=from_email,
        recipient_list=[restaurant.email],
        fail_silently=False,
    )
    return redirect('order_success')

@login_required(login_url='login')
def orders(request):
    """
    This view is used to render the orders page
    """
    customer = request.user.customer
    orders = Order.objects.filter(customer=customer)
    return render(request, 'orders.html', {'orders':orders})

def logout(request):
    """
    This view is used to log a user out
    """
    auth_logout(request)
    return redirect('login')

def register(request):
    """
    This view is used to register a customer
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('login')
        
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    """
    This view is used to login a customer
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')
            return render(request, 'login.html')
    else:
        return render(request, 'login.html')
  

def menu(request):
    """
    This view is used to render the menu page of a restaurant
    """
    products = Product.objects.all()
    return render(request, 'menu.html', {'products': products})

@login_required(login_url="login")
def checkout(request, id):
    """
    This view is used to render the checkout page
    """
    food = get_object_or_404(Product, pk=id)
    return render(request, 'checkout.html', {'food':food})

@login_required(login_url="login")
def cart_checkout(request):
    """
    This view is used to handle the cart checkout
    """
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': product.price * quantity
        })
        total_price += product.price * quantity

    # Here, you'd typically handle the payment and order confirmation
    return render(request, 'cart_checkout.html', {'cart_items': cart_items, 'total_price': total_price})


def restaurants(request):
    """
    This view is used to render the restaurants display page
    """
    restaurants = Restaurant.objects.all()
    return render(request, 'restaurants.html', {'restaurants': restaurants})

def product(request, id):
    """
    This view is used to display the products page
    """
    return render(request, 'product.html')

def restaurant(request, id):
    """
    This view is used to render the individual restaurant page
    """
    restaurant = get_object_or_404(Restaurant, pk=id)
    menus = restaurant.menu_items.all()
    context = {
        'restaurant': restaurant, 
        'menus': menus,
    }
    return render(request, 'restaurant.html', context)

def process_checkout(request, id):
    """
    This view is used to process mpesa payments
    """
    food = get_object_or_404(Product, pk=id)

    if request.method == 'POST':
        amount = food.price
        raw_phone = request.POST.get('phone', '').strip()
        phone_number = normalize_phone(raw_phone)

        if not phone_number:
            return HttpResponse('Invalid phone number format. Use 07XXXXXXXX or +2547XXXXXXXX.')

        # Get access token
        try:
            access_token = get_access_token()
        except Exception as e:
            return HttpResponse(f"Failed to get access token: {e}")

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        passkey = settings.MPESA_PASSKEY
        shortcode = settings.MPESA_EXPRESS_SHORTCODE

        data_to_encode = shortcode + passkey + timestamp
        encoded_password = base64.b64encode(data_to_encode.encode()).decode()

        payload = {
            "BusinessShortCode": shortcode,
            "Password": encoded_password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": "https://3552-102-0-12-54.ngrok-free.app/mpesa-callback/", # can only be used in production
            "AccountReference": "Tumanow",
            "TransactionDesc": "Paying for food"
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers=headers
        )

        res_data = response.json()

        if res_data.get('ResponseCode') == '0':
            STKPushTransaction.objects.create(
                phone_number=phone_number,
                amount=amount,
                description="Paying for food",
                checkout_request_id=res_data.get('CheckoutRequestID'),
                merchant_request_id=res_data.get('MerchantRequestID'),
                status='pending'
            )
            return render(request, 'processing.html', {'food': food, 'checkout_request_id': res_data.get('CheckoutRequestID')})
        else:
            return HttpResponse(f"Failed to initiate payment: {res_data.get('errorMessage', 'Unknown error')}")

    return render(request, 'checkout.html', {'food': food})


@csrf_exempt
def mpesa_callback(request):
    """
    This view is the call back url for mpesa(usable only in production)
    """
    if request.method == 'POST':
        try:
        
            # Parse the callback data
            data = json.loads(request.body)
            callback = data['Body']['stkCallback']
            result_code = callback['ResultCode']
            result_desc = callback.get('ResultDesc', '')
            checkout_id = callback.get('CheckoutRequestID')

            # Retrieve transaction from DB using CheckoutRequestID
            txn = STKPushTransaction.objects.filter(checkout_request_id=checkout_id).first()
            if not txn:
                return JsonResponse({'error': 'Transaction not found'}, status=404)

            # Update transaction status based on result code
            if result_code == 0:
                metadata = {item['Name']: item.get('Value') for item in callback['CallbackMetadata']['Item']}
                txn.mpesa_receipt_number = metadata.get('MpesaReceiptNumber')
                txn.transaction_date = datetime.strptime(str(metadata.get('TransactionDate')), "%Y%m%d%H%M%S")
                txn.status = 'success'
            else:
                txn.status = 'failed'

            txn.result_code = result_code
            txn.result_desc = result_desc
            txn.save()

            return JsonResponse({'status': 'ok'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'message': 'Callback expects POST'}, status=405)


def check_payment_status(request):
    """
    This view is used to check payment status(usable only in production)
    """
    checkout_id = request.GET.get('checkout_id')
    if not checkout_id:
        return JsonResponse({'status': 'missing_checkout_id'})

    txn = STKPushTransaction.objects.filter(checkout_request_id=checkout_id).first()
    if not txn:
        return JsonResponse({'status': 'not_found'})

    return JsonResponse({
        'status': txn.status,
        'amount': txn.amount,
        'receipt': txn.mpesa_receipt_number,
        'phone': txn.phone_number,
        'description': txn.description,
        'timestamp': txn.transaction_date.strftime("%Y-%m-%d %H:%M:%S") if txn.transaction_date else None
    })


@login_required(login_url='login')
def add_to_cart(request, id):
    """
    This view is used to add a food to cart
    """
    product = get_object_or_404(Product, id=id)
    cart = request.session.get('cart', {})
    cart[str(product.id)] = cart.get(str(product.id), 0) + 1
    request.session['cart'] = cart
    return redirect('view_cart') 


@login_required(login_url='login')
def view_cart(request):
    """
    This view is used to view items in a cart
    """
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': product.price * quantity
        })
        total_price += product.price * quantity

    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})