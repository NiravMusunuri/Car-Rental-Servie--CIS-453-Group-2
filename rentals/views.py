from django.shortcuts import get_object_or_404, redirect, render
from .models import Car, Category, Booking
from .forms import BookingForm

def car_list(request):
    cars = Car.objects.filter(status='available')
    categories = Category.objects.all()

    selected_category = request.GET.get('category')
    transmission = request.GET.get('transmission')

    if selected_category:
        cars = cars.filter(category_id=selected_category)

    if transmission:
        cars = cars.filter(transmission__iexact=transmission)

    context = {
        'cars': cars,
        'categories': categories,
        'selected_category': selected_category,
        'selected_transmission': transmission,
    }

    return render(request, 'rentals/car_list.html', context)
def book_car(request, car_id):
    car = get_object_or_404(Car, id=car_id, status='available')

    if request.method == 'POST':
        form = BookingForm(request.POST)

        if form.is_valid():
            pickup_date = form.cleaned_data['pickup_date']
            return_date = form.cleaned_data['return_date']

            overlapping_booking = Booking.objects.filter(
                car=car,
                pickup_date__lt=return_date,
                return_date__gt=pickup_date
            ).exists()

            if overlapping_booking:
                form.add_error(
                    None,
                    'This car is already booked for the selected dates.'
                )
            else:
                booking = form.save(commit=False)
                booking.car = car
                booking.save()

                return redirect('booking_success')

    else:
        form = BookingForm()

    return render(
        request,
        'rentals/book_car.html',
        {
            'car': car,
            'form': form,
        }
    )

def booking_success(request):
    return render(request, 'rentals/booking_success.html')
