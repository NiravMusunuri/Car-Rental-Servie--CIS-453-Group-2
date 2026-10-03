from django.contrib.auth import views as auth
from django.urls import path
from . import views
urlpatterns = [
    path("",views.car_list,name="home"),
    path("cars/",views.car_list,name="car_list"),
    path("cars/<int:car_id>/",views.car_detail,name="car_detail"),
    path("cars/<int:car_id>/book/",views.book_car,name="book_car"),
    path("register/",views.register,name="register"),
    path("login/",auth.LoginView.as_view(template_name="rentals/login.html"),name="login"),
    path("logout/",auth.LogoutView.as_view(),name="logout"),
    path("profile/",views.profile,name="profile"),
    path("bookings/",views.my_bookings,name="my_bookings"),
    path("bookings/<int:booking_id>/",views.booking_detail,name="booking_detail"),
    path("bookings/<int:booking_id>/pay/",views.pay,name="pay"),
    path("bookings/<int:booking_id>/cancel/",views.cancel,name="cancel"),
    path("bookings/<int:booking_id>/modify/",views.modify,name="modify"),
]
