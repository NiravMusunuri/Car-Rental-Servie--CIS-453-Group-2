from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import IntegrityError, OperationalError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .models import Booking, Car, Profile
from .forms import RegistrationForm, ProfileForm, DateForm, CatalogForm, MockPaymentForm

def notify(booking, action):
    send_mail(f"Rental {action}: #{booking.pk}", f"{booking.car}\n{booking.pickup_date} to {booking.return_date}\nTotal: ${booking.total_price}\nStatus: {booking.status}; payment: {booking.payment_status}\nLocal prototype: no actual payment.", None, [booking.customer_email], fail_silently=True)

def register(request):
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            user = form.save()
        except IntegrityError:
            form.add_error(None,"An account with this username or email already exists.")
        else:
            login(request,user)
            messages.success(request,"Your account is ready.")
            return redirect("car_list")
    return render(request,"rentals/form.html",{"form":form,"title":"Create your account","button":"Register"})

@login_required
def profile(request):
    item, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None,instance=item)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request,"Profile saved.")
        return redirect("profile")
    return render(request,"rentals/form.html",{"form":form,"title":"Customer profile","button":"Save profile"})

def car_list(request):
    form = CatalogForm(request.GET)
    cars = Car.objects.select_related("category").order_by("make","model")
    if form.is_valid():
        data = form.cleaned_data
        if data.get("category"): cars = cars.filter(category=data["category"])
        if data.get("transmission"): cars = cars.filter(transmission=data["transmission"])
        unavailable = Booking.objects.filter(status="confirmed")
        if data.get("pickup_date"):
            unavailable = unavailable.filter(pickup_date__lt=data["return_date"],return_date__gt=data["pickup_date"])
            blocked_ids = unavailable.values("car_id")
        else:
            blocked_ids = []
        from django.db.models import Q
        available = Q(status="available") & ~Q(pk__in=blocked_ids)
        if data.get("availability") == "available": cars = cars.filter(available)
        if data.get("availability") == "unavailable": cars = cars.exclude(available)
        blocked = set(blocked_ids.values_list("car_id",flat=True)) if hasattr(blocked_ids,"values_list") else set()
        for car in cars:
            car.search_available = car.status == "available" and car.pk not in blocked
    else:
        cars = cars.none()
    return render(request,"rentals/car_list.html",{"cars":cars,"form":form})

def car_detail(request, car_id):
    car = get_object_or_404(Car.objects.select_related("category"),pk=car_id)
    return render(request,"rentals/car_detail.html",{"car":car})

@login_required
def book_car(request, car_id):
    car = get_object_or_404(Car.objects.select_related("category"),pk=car_id)
    form = DateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            booking = Booking(car=car,customer=request.user,customer_name=request.user.get_full_name() or request.user.username,customer_email=request.user.email,**form.cleaned_data)
            booking.save()
        except ValidationError as exc:
            form.add_error(None,exc)
        except OperationalError:
            form.add_error(None,"The database is busy. Please try again.")
        else:
            messages.success(request,"Dates reserved. Complete the mock payment below.")
            return redirect("booking_detail", booking_id=booking.pk)
    return render(request,"rentals/form.html",{"form":form,"car":car,"title":f"Reserve {car}","button":"Reserve dates"})

@login_required
def my_bookings(request):
    return render(request,"rentals/my_bookings.html",{"bookings":request.user.bookings.select_related("car")})

@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking.objects.select_related("car"),pk=booking_id,customer=request.user)
    return render(request,"rentals/booking_detail.html",{"booking":booking,"payment_form":MockPaymentForm()})

@login_required
@require_POST
def pay(request, booking_id):
    form = MockPaymentForm(request.POST)
    with transaction.atomic():
        booking = get_object_or_404(Booking,pk=booking_id,customer=request.user)
        if booking.status != "confirmed" or booking.payment_status != "unpaid":
            messages.info(request,"This booking does not need payment.")
        elif form.is_valid():
            if form.cleaned_data["result"] == "success":
                booking.payment_status = "paid"
                booking.save()
                transaction.on_commit(lambda: notify(booking,"confirmed"))
                messages.success(request,"Mock payment approved. Your booking is confirmed.")
            else:
                messages.error(request,"Mock payment declined. Retry or cancel to release the dates.")
        else:
            return render(request,"rentals/booking_detail.html",{"booking":booking,"payment_form":form})
    return redirect("booking_detail",booking_id=booking.pk)

@login_required
@require_POST
def cancel(request, booking_id):
    with transaction.atomic():
        booking = get_object_or_404(Booking,pk=booking_id,customer=request.user)
        if not booking.can_change:
            messages.error(request,"Only confirmed bookings with a future pickup can be cancelled.")
        else:
            booking.status = "cancelled"
            booking.save()
            transaction.on_commit(lambda: notify(booking,"cancelled"))
            messages.success(request,"Booking cancelled. Any mock payment has been marked refunded.")
    return redirect("booking_detail",booking_id=booking.pk)

@login_required
def modify(request, booking_id):
    booking = get_object_or_404(Booking,pk=booking_id,customer=request.user)
    form = DateForm(request.POST or None,initial={"pickup_date":booking.pickup_date,"return_date":booking.return_date})
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                booking = get_object_or_404(Booking,pk=booking_id,customer=request.user)
                if not booking.can_change:
                    raise ValidationError("Only future confirmed bookings can be changed.")
                booking.pickup_date = form.cleaned_data["pickup_date"]
                booking.return_date = form.cleaned_data["return_date"]
                booking.payment_status = "unpaid"
                booking.save()
                transaction.on_commit(lambda: notify(booking,"modified"))
        except ValidationError as exc:
            form.add_error(None,exc)
        except OperationalError:
            form.add_error(None,"Database busy. Please try again.")
        else:
            messages.success(request,"Dates updated at your original rate. Complete mock payment for the revised total.")
            return redirect("booking_detail",booking_id=booking.pk)
    return render(request,"rentals/form.html",{"form":form,"car":booking.car,"title":f"Change booking #{booking.pk}","button":"Save revised dates"})
