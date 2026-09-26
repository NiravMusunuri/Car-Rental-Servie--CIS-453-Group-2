from datetime import date

from django import forms

from .models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            'customer_name',
            'customer_email',
            'pickup_date',
            'return_date',
        ]

        widgets = {
            'pickup_date': forms.DateInput(attrs={'type': 'date'}),
            'return_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()

        pickup_date = cleaned_data.get('pickup_date')
        return_date = cleaned_data.get('return_date')

        if pickup_date and pickup_date < date.today():
            self.add_error(
                'pickup_date',
                'Pickup date cannot be in the past.'
            )

        if pickup_date and return_date and return_date <= pickup_date:
            self.add_error(
                'return_date',
                'Return date must be after the pickup date.'
            )

        return cleaned_data
