from django.contrib import admin
from .models import Vendor, Product, Restaurant, Customer, STKPushTransaction, Deliverer, Order
from django.core.mail import send_mail
from django.utils.html import format_html
from django.conf import settings
from django import forms
from django.contrib import messages
from django.shortcuts import render
from datetime import datetime
from django.http import HttpResponseRedirect
import base64
from django.urls import path, reverse
import requests
from .utils import get_access_token, normalize_phone  # Ensure this import points to the correct module
from django.shortcuts import redirect
from django.template.response import TemplateResponse

# Register your models here.


admin.site.site_header = "Tumanow Admin"
admin.site.site_title = "Tumanow Admin Portal"
admin.site.index_title = "Welcome to Tumanow Admin"
admin.site.register(STKPushTransaction)

@admin.register(Order)
class AdminOrder(admin.ModelAdmin):
    list_display = ['status','customer', 'restaurant', 'vendor', 'deliverer', 'stkpush_action']

    def get_changelist_instance(self, request):
        self._request = request
        return super().get_changelist_instance(request)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:order_id>/stkpush/',
                self.admin_site.admin_view(self.initiate_stkpush),
                name='initiate-stkpush',
            ),
        ]
        return custom_urls + urls


    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        
        # Filter by vendor if the user is a vendor
        if hasattr(request.user, 'vendor'):
            return qs.filter(vendor=request.user.vendor)
        
        # Filter by deliverer if the user is a deliverer
        if hasattr(request.user, 'deliverer'):
            return qs.filter(deliverer=request.user.deliverer)
        
        return qs.none()

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return []

        all_fields = [field.name for field in self.model._meta.fields]

        if hasattr(request.user, 'deliverer'):
            # Deliverer can only edit 'status'
            return [field for field in all_fields if field != 'status']

        if hasattr(request.user, 'vendor'):
            # Vendor can edit 'status' and 'deliverer'
            editable_fields = ['status', 'deliverer']
            return [field for field in all_fields if field not in editable_fields]

        # Everyone else: read-only
        return all_fields

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        if hasattr(request.user, 'vendor') and obj.vendor.user == request.user:
            return True
        if hasattr(request.user, 'deliverer') and obj.deliverer and obj.deliverer.user == request.user:
            return True
        return False

    def save_model(self, request, obj, form, change):
        notify_deliverer = False
        notify_customer = False

        if change:
            old_obj = Order.objects.get(pk=obj.pk)
            # Deliverer was changed or newly assigned
            if old_obj.deliverer != obj.deliverer and obj.deliverer and obj.deliverer.user.email:
                notify_deliverer = True
                notify_customer = True
        else:
            # New object and deliverer is assigned
            if obj.deliverer and obj.deliverer.user.email:
                notify_deliverer = True
                notify_customer = True

        # Send email to deliverer
        if notify_deliverer:
            send_mail(
                subject='New Delivery Assignment',
                message=f"You have been assigned to deliver Order #{obj.pk}.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[obj.deliverer.user.email],
                fail_silently=False,
            )

        # Send email to customer
        if notify_customer and obj.customer.email:
            deliverer_name = obj.deliverer.name
            deliverer_phone = obj.deliverer.phone_number
            order_status = obj.get_status_display()
            send_mail(
                subject='Your Order Has Been Assigned a Deliverer',
                message=(
                    f"Good news! Your order #{obj.pk} has been assigned to a deliverer.\n\n"
                    f"Deliverer Name: {deliverer_name}\n"
                    f"Phone Number: {deliverer_phone}\n"
                    f"Delivery Status: {order_status}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[obj.customer.email],
                fail_silently=False,
            )

        # Save the object
        super().save_model(request, obj, form, change)


    def initiate_stkpush(self, request, order_id):
        from django.shortcuts import get_object_or_404
        from django.http import HttpResponseRedirect
        order = get_object_or_404(Order, pk=order_id)

        if not hasattr(request.user, 'deliverer') or order.deliverer.user != request.user:
            self.message_user(request, "You do not have permission to initiate payment for this order.", level=messages.ERROR)
            return redirect('..')
        if order.status != 'A':
            self.message_user(request, "Order must be marked as 'received' before initiating payment.", level=messages.WARNING)
            return redirect('..')

        try:
            # Normalize phone and send STK push
            phone = str(order.customer.phone_number)
            amount = order.product.price  
            description = f"Payment for Order #{order.id}"

            access_token = get_access_token()
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
                "PartyA": phone,
                "PartyB": shortcode,
                "PhoneNumber": phone,
                "CallBackURL": "https://your-ngrok-url.ngrok-free.app/mpesa-callback/",
                "AccountReference": "Tumanow",
                "TransactionDesc": description
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

            if response.status_code == 200:
                self.message_user(request, "STK Push initiated successfully.", level=messages.SUCCESS)
            else:
                self.message_user(request, f"Failed to initiate STK Push: {response.text}", level=messages.ERROR)

        except Exception as e:
            self.message_user(request, f"Error: {str(e)}", level=messages.ERROR)

        messages.success(request, f"STK Push initiated for order {order.pk}.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))
    
    def stkpush_action(self, obj):
        request = getattr(self, '_request', None)
        if not request:
            return '-'

        user = request.user
        is_deliverer = hasattr(user, 'deliverer')
        is_assigned = obj.deliverer and obj.deliverer.user == user
        if is_deliverer and is_assigned and obj.status == 'A':
            url = reverse('admin:initiate-stkpush', args=[obj.pk])
            return format_html('<a class="button" href="{}">Send STK Push</a>', url)
        return '-'
    stkpush_action.short_description = "STK Push"

class DelivererForm(forms.ModelForm):
    class Meta:
        model = Deliverer
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        vendor_users = Vendor.objects.values_list('user_id', flat=True)
        self.fields['user'].queryset = self.fields['user'].queryset.exclude(id__in=vendor_users)


@admin.register(Deliverer)
class AdminDeliverer(admin.ModelAdmin):
    form = DelivererForm
    list_display = ['name', 'restaurant', 'phone_number', 'status']
    

    def has_change_permission(self, request, obj=None):
        # Allow change only if the user is the related vendor or superuser
        if request.user.is_superuser:
            return True
        if obj is None:
            return True  # allow access to list page
        return obj.vendor.user == request.user

@admin.register(Customer)
class AdminCustomer(admin.ModelAdmin):
    list_display = ['profile_pic_display','name', 'username', 'email']
    def profile_pic_display(self, obj):
        if obj.profile_pic: 
            return format_html('<img src="{}" width="120" height="120" style="object-fit: cover;"/>', obj.profile_pic.url)
        return "No Image"
    

    profile_pic_display.allow_tags = True
    profile_pic_display.short_description = "Image" 

@admin.register(Restaurant)
class AdminRestaurant(admin.ModelAdmin):
    list_display = ['name', 'image_display', 'email','phone_number']

    def image_display(self, obj):
        if obj.image: 
            return format_html('<img src="{}" width="120" height="120" style="object-fit: cover;"/>', obj.image.url)
        return "No Image"
    

    image_display.allow_tags = True
    image_display.short_description = "Image" 

class VendorForm(forms.ModelForm):
    class Meta:
        model = Deliverer
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        deliverer_users = Deliverer.objects.values_list('user_id', flat=True)
        self.fields['user'].queryset = self.fields['user'].queryset.exclude(id__in=deliverer_users)

@admin.register(Vendor)
class AdminVendor(admin.ModelAdmin):
    form = VendorForm
    list_display = ['vendor_name', 'restaurant', 'phone_number']

@admin.register(Product)
class AdminProduct(admin.ModelAdmin):
    list_display = ['vendor', 'name', 'price', 'image_display', 'restaurant']

    def image_display(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="120" height="120" style="object-fit: cover;"/>', obj.image.url)
        return "No Image"

    image_display.short_description = "Image"
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # show all orders to superusers
        elif hasattr(request.user, 'vendor'):
            return qs.filter(vendor=request.user.vendor)
        return qs.none()  # non-vendors see nothing
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "vendor" and not request.user.is_superuser:
            try:
                vendor = Vendor.objects.get(user=request.user)
                kwargs["queryset"] = Vendor.objects.filter(id=vendor.id)
            except Vendor.DoesNotExist:
                kwargs["queryset"] = Vendor.objects.none()

        if db_field.name == "restaurant" and not request.user.is_superuser:
            try:
                vendor = Vendor.objects.get(user=request.user)
                kwargs["queryset"] = Restaurant.objects.filter(id=vendor.restaurant.id)
            except Vendor.DoesNotExist:
                kwargs["queryset"] = Restaurant.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.vendor_id and not request.user.is_superuser:
            try:
                obj.vendor = Vendor.objects.get(user=request.user)
            except Vendor.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)

    def image_display(self, obj):
        if obj.image: 
            return format_html('<img src="{}" width="120" height="120" style="object-fit: cover;"/>', obj.image.url)
        return "No Image"
    

    image_display.allow_tags = True
    image_display.short_description = "Image" 


