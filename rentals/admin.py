from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Car, Booking, Profile
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name","daily_rate")
@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ("make","model","year","category","seats","transmission","status")
    list_filter = ("category","status")
    search_fields = ("make","model")
    readonly_fields = ("image_preview",)
    @admin.display(description="Current uploaded photo")
    def image_preview(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" alt="Car photo" style="max-width:320px;max-height:180px;object-fit:contain">', obj.image.url)
        return "No uploaded photo; the sample image or placeholder is shown."
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id","customer_name","car","pickup_date","return_date","status","total_price","payment_status")
    list_filter = ("status","payment_status","pickup_date")
    search_fields = ("customer_name","customer_email","car__make","car__model")
    readonly_fields = ("created_at","daily_rate","total_price","payment_status")
    # Bookings are retained for audit; cancel instead of delete.
    def has_delete_permission(self, request, obj=None):
        return False
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user","phone")
