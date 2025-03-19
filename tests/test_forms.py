# aws_ec2/tests/test_forms.py
from django.test import TestCase
from django.utils import timezone
import datetime

from aws_ec2.forms import BookingForm


class BookingFormTestCase(TestCase):
    def test_valid_form(self):
        """Test that form is valid with correct data"""
        # Create form data with future date
        future_time = timezone.now() + datetime.timedelta(days=1)
        form_data = {
            'email': 'test@example.com',
            'booking_time': future_time.strftime('%Y-%m-%dT%H:%M'),
            'number_of_users': 5
        }
        
        form = BookingForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_email(self):
        """Test form validation with invalid email"""
        future_time = timezone.now() + datetime.timedelta(days=1)
        form_data = {
            'email': 'invalid-email',  # Invalid email format
            'booking_time': future_time.strftime('%Y-%m-%dT%H:%M'),
            'number_of_users': 5
        }
        
        form = BookingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_past_booking_time(self):
        """Test form validation with past booking time"""
        past_time = timezone.now() - datetime.timedelta(hours=1)
        form_data = {
            'email': 'test@example.com',
            'booking_time': past_time.strftime('%Y-%m-%dT%H:%M'),
            'number_of_users': 5
        }
        
        form = BookingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('booking_time', form.errors)
    
    def test_negative_users(self):
        """Test form validation with negative number of users"""
        future_time = timezone.now() + datetime.timedelta(days=1)
        form_data = {
            'email': 'test@example.com',
            'booking_time': future_time.strftime('%Y-%m-%dT%H:%M'),
            'number_of_users': -1  # Negative value
        }
        
        form = BookingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('number_of_users', form.errors)
    
    def test_too_many_users(self):
        """Test form validation with excessive number of users"""
        future_time = timezone.now() + datetime.timedelta(days=1)
        form_data = {
            'email': 'test@example.com',
            'booking_time': future_time.strftime('%Y-%m-%dT%H:%M'),
            'number_of_users': 100  # Above maximum
        }
        
        form = BookingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('number_of_users', form.errors)
    
    def test_empty_form(self):
        """Test form validation with empty data"""
        form = BookingForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 3)  # All three fields should have errors