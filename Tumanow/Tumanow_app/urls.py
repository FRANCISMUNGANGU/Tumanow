from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('profile', views.profile, name='profile'),
    path('menu/', views.menu, name='menu'),
    path('checkout/<int:id>', views.checkout, name='checkout'),
    path('restaurants/', views.restaurants, name='restaurants'),
    path('product/<int:id>', views.product, name='product'),
    path('restaurant/<int:id>/', views.restaurant, name='restaurant'),
    path('process_checkout/<int:id>/', views.process_checkout, name='process_checkout'),
    path('check-payment-status/', views.check_payment_status, name='check_payment_status'),
    path('mpesa-callback/', views.mpesa_callback, name='mpesa_callback'),
    path('place_order/<int:id>', views.place_order, name='place_order'),
    path('profile-url/', views.profile_page, name='profile_page'),
    path('logout/', views.logout, name='logout'),
    path('orders/', views.orders, name='order_success'),
    path('cart/add/<int:id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart-checkout/', views.cart_checkout, name='cart-checkout'),
]