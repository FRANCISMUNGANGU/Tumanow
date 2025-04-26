from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login as auth_login
from .models import Restaurant, Product, Customer
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm

# Create your views here.
def home(request):
    return render(request, "index.html")

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile_pic = request.FILES.get('profile_pic')
            phone_number = form.cleaned_data.get('phone_number')
            Customer.objects.create(
                customer=user,
                name=user.first_name,
                username=user.username,
                email=user.email,
                profile_pic=profile_pic,
                phone_number=phone_number
            )
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def login(request):
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

@login_required(login_url='login')
def checkout(request, id):
    food = get_object_or_404(Product, pk=id)
    return render(request, 'checkout.html', {'food':food})

def restaurants(request):
    restaurants = Restaurant.objects.all()
    return render(request, 'restaurants.html', {'restaurants': restaurants})

def product(request, id):
    return render(request, 'product.html')

@login_required(login_url='login')
def profile(request):
    customer = request.user.customer  # Assuming OneToOne relation with User
    return render(request, 'index.html', {'customer': customer})

def restaurant(request, id):
    restaurant = get_object_or_404(Restaurant, pk=id)
    menus = restaurant.menu_items.all()
    context = {
        'restaurant': restaurant, 
        'menus': menus,
    }
    return render(request, 'restaurant.html', context)

def process_checkout(request):
    pass