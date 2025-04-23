from django.contrib import admin
from .models import Vendor, Product, Restaurant
from django.utils.html import format_html
# Register your models here.

# admin.site.register(Vendor)

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
    list_display = ['vendor', 'name', 'price', 'image_display']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "vendor" and not request.user.is_superuser:
            try:
                # Assuming there's a one-to-one or foreign key from User to Vendor
                vendor = Vendor.objects.get(user=request.user)
                kwargs["queryset"] = Vendor.objects.filter(id=vendor.id)
            except Vendor.DoesNotExist:
                kwargs["queryset"] = Vendor.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def image_display(self, obj):
        if obj.image: 
            return format_html('<img src="{}" width="120" height="120" style="object-fit: cover;"/>', obj.image.url)
        return "No Image"
    

    image_display.allow_tags = True
    image_display.short_description = "Image" 