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
    path('process_checkout', views.process_checkout, name='process_checkout'),
]