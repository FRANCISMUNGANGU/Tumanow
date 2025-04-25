from django.contrib import admin
from .models import Vendor, Product, Restaurant, Customer
from django.utils.html import format_html
# Register your models here.


admin.site.site_header = "Tumanow Admin"
admin.site.site_title = "Tumanow Admin Portal"
admin.site.index_title = "Welcome to Tumanow Admin"

@admin.register(Customer)
class AdminCustomer(admin.ModelAdmin):
    list_display = ['profile_pic_display','name', 'username']
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

@admin.register(Vendor)
class AdminVendor(admin.ModelAdmin):
    list_display = ['vendor_name', 'restaurant', 'phone_number']

@admin.register(Product)
class AdminProduct(admin.ModelAdmin):
    list_display = ['vendor', 'name', 'price', 'image_display', 'restaurant']

    def image_display(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="120" height="120" style="object-fit: cover;"/>', obj.image.url)
        return "No Image"

    image_display.short_description = "Image"

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
        # Auto-assign vendor for non-superusers
        if not obj.vendor_id and not request.user.is_superuser:
            try:
                obj.vendor = Vendor.objects.get(user=request.user)
            except Vendor.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)
