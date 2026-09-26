from django.contrib import admin
from .models import Category, Car, Booking


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'daily_rate')


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = (
        'make',
        'model',
        'year',
        'category',
        'seats',
        'transmission',
        'status',
    )

    list_filter = ('category', 'status')
    search_fields = ('make', 'model')
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'customer_name',
        'customer_email',
        'car',
        'pickup_date',
        'return_date',
        'created_at',
    )

    search_fields = (
        'customer_name',
        'customer_email',
        'car__make',
        'car__model',
    )

    list_filter = (
        'pickup_date',
        'return_date',
    )
