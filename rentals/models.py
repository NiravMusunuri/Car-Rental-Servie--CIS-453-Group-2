from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Car(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('maintenance', 'Maintenance'),
    ]

    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='cars'
    )
    seats = models.IntegerField()
    transmission = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available'
    )

    def __str__(self):
        return f"{self.year} {self.make} {self.model}"
class Booking(models.Model):
    car = models.ForeignKey(
        Car,
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    pickup_date = models.DateField()
    return_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.car}"
