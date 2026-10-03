from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.utils import timezone
from .models import AccountEmail, Profile, Category
User = get_user_model()

class RegistrationForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=70)
    last_name = forms.CharField(max_length=70)
    class Meta:
        model = User
        fields = ["username","first_name","last_name","email","password1","password2"]
    def clean_username(self):
        value = self.cleaned_data["username"].strip().lower()
        if User.objects.filter(username__iexact=value).exists():
            raise forms.ValidationError("An account with this username already exists.")
        return value
    def clean_email(self):
        value = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=value).exists() or AccountEmail.objects.filter(email=value).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return value
    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.save()
        AccountEmail.objects.create(user=user,email=user.email)
        Profile.objects.create(user=user)
        return user

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["phone","address"]

class DateForm(forms.Form):
    pickup_date = forms.DateField(widget=forms.DateInput(attrs={"type":"date"}))
    return_date = forms.DateField(widget=forms.DateInput(attrs={"type":"date"}))
    def clean(self):
        data = super().clean()
        start, end = data.get("pickup_date"), data.get("return_date")
        if start and start < timezone.localdate():
            self.add_error("pickup_date","Pickup cannot be in the past.")
        if start and end and end <= start:
            self.add_error("return_date","Return must be after pickup.")
        return data

class CatalogForm(DateForm):
    pickup_date = forms.DateField(required=False,widget=forms.DateInput(attrs={"type":"date"}))
    return_date = forms.DateField(required=False,widget=forms.DateInput(attrs={"type":"date"}))
    category = forms.ModelChoiceField(queryset=Category.objects.all(),required=False,empty_label="All categories")
    transmission = forms.ChoiceField(required=False,choices=[("","Any transmission"),("Automatic","Automatic"),("Manual","Manual")])
    availability = forms.ChoiceField(required=False,choices=[("","All cars"),("available","Available for rental"),("unavailable","Unavailable")])
    def clean(self):
        data = super().clean()
        if bool(data.get("pickup_date")) != bool(data.get("return_date")):
            raise forms.ValidationError("Enter both pickup and return dates to search a date range.")
        return data

class MockPaymentForm(forms.Form):
    result = forms.ChoiceField(label="Simulated payment outcome", choices=[("success","Approve mock payment"),("declined","Decline mock payment")])
    consent = forms.BooleanField(label="I understand this is a demo payment. No money will be charged.")
