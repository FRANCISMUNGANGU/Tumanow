from django.contrib import admin
from .models import Vendor, Product, Restaurant, Customer, STKPushTransaction, Deliverer, Order
from django.core.mail import send_mail
from django.utils.html import format_html
from django.conf import settings
from django import forms
# Register your models here.


admin.site.site_header = "Tumanow Admin"
admin.site.site_title = "Tumanow Admin Portal"
admin.site.index_title = "Welcome to Tumanow Admin"
admin.site.register(STKPushTransaction)

@admin.register(Order)
class AdminOrder(admin.ModelAdmin):
    list_display = ['status','customer', 'restaurant', 'vendor', 'deliverer']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif hasattr(request.user, 'vendor'):
            return qs.filter(vendor=request.user.vendor)
        elif hasattr(request.user, 'deliverer'):
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

