from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    def __str__(self):
        return self.name

class Car(models.Model):
    STATUS_CHOICES = [("available","Available"),("reserved","Reserved / blocked"),("maintenance","Maintenance")]
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField(validators=[MinValueValidator(1900)])
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="cars")
    seats = models.IntegerField(validators=[MinValueValidator(1)])
    transmission = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")
    image = models.ImageField(upload_to="cars/", blank=True, help_text="Upload a JPG, PNG or WebP car photo. Clear it to restore the sample image.")
    @property
    def image_path(self):
        images = {
            ("bmw", "330i"): "bmw-330i",
            ("ford", "explorer"): "ford-explorer",
            ("honda", "fit"): "honda-fit",
            ("mercedes-benz", "c-class"): "mercedes-c-class",
            ("toyota", "corolla"): "toyota-corolla",
            ("toyota", "rav4"): "toyota-rav4",
        }
        slug = images.get((self.make.lower(), self.model.lower()))
        return f"rentals/images/{slug}.png" if slug else ""
    def __str__(self):
        return f"{self.year} {self.make} {self.model}"

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=250, blank=True)
    def __str__(self):
        return self.user.username

class AccountEmail(models.Model):
    # Normalized identity registry supplies a DB-level duplicate-email guarantee.
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email = models.EmailField(unique=True)

class Booking(models.Model):
    STATUS_CHOICES = [("confirmed","Confirmed"),("cancelled","Cancelled")]
    car = models.ForeignKey(Car, on_delete=models.PROTECT, related_name="bookings")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings", null=True, blank=True)
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    pickup_date = models.DateField()
    return_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="confirmed")
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=[("unpaid","Awaiting mock payment"),("paid","Mock paid"),("refunded","Mock refunded")], default="unpaid")
    class Meta:
        ordering = ["-created_at"]
        constraints = [models.CheckConstraint(condition=models.Q(return_date__gt=models.F("pickup_date")), name="return_after_pickup")]
    @property
    def days(self):
        return (self.return_date-self.pickup_date).days
    @property
    def can_change(self):
        return self.status == "confirmed" and self.pickup_date > timezone.localdate()
    def clean(self):
        super().clean()
        if not self.pickup_date or not self.return_date:
            return
        if self.return_date <= self.pickup_date:
            raise ValidationError("Return date must be after pickup.")
        old = type(self).objects.filter(pk=self.pk).first() if self.pk else None
        changed = not old or any(getattr(old,k) != getattr(self,k) for k in ["car_id","pickup_date","return_date"])
        if changed and self.pickup_date < timezone.localdate():
            raise ValidationError("Pickup cannot be in the past.")
        if self.status == "confirmed" and self.car_id:
            if self.car.status != "available" and (changed or (old and old.status != "confirmed")):
                raise ValidationError("This car is blocked or in maintenance.")
            if type(self).objects.filter(car_id=self.car_id, status="confirmed", pickup_date__lt=self.return_date, return_date__gt=self.pickup_date).exclude(pk=self.pk).exists():
                raise ValidationError("This car is already booked for the selected dates.")
    def save(self, *args, **kwargs):
        # SQLite IMMEDIATE acquires the write lock before conflict validation.
        with transaction.atomic():
            old = type(self).objects.filter(pk=self.pk).first() if self.pk else None
            self.full_clean()
            if not old or old.car_id != self.car_id:
                self.daily_rate = self.car.category.daily_rate
            self.total_price = self.daily_rate * self.days
            self._meta.get_field("total_price").clean(self.total_price, self)
            if self.status == "cancelled" and self.payment_status == "paid":
                self.payment_status = "refunded"
            super().save(*args, **kwargs)
    def __str__(self):
        return f"Booking #{self.pk} — {self.car}"
