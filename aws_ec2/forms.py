# aws_ec2/forms.py
from django import forms
from django.core.exceptions import ValidationError
from datetime import datetime
from django.utils import timezone

class BookingForm(forms.Form):
    email = forms.EmailField(label='Email', required=True)
    booking_time = forms.DateTimeField(
        label='Booking Time',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'step': '900'}),  # Step set to 900 seconds (15 minutes)
        input_formats=['%Y-%m-%dT%H:%M'],  # Format for datetime-local
    )
    number_of_users = forms.IntegerField(label='Number of Users', min_value=1, max_value=50)

    def clean_booking_time(self):
        booking_time = self.cleaned_data.get('booking_time')
        
        # Make the booking_time timezone-aware
        if booking_time.tzinfo is None:
            booking_time = timezone.make_aware(booking_time)
        
        # Compare with the current time
        if booking_time <= timezone.now():
            raise ValidationError("Booking time must be in the future.")
        
        return booking_time
