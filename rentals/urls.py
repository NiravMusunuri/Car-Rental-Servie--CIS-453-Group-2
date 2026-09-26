from django.urls import path
from . import views

urlpatterns = [
    path('cars/', views.car_list, name='car_list'),
    path('cars/<int:car_id>/book/', views.book_car, name='book_car'),
    path('booking/success/', views.booking_success, name='booking_success'),
]
