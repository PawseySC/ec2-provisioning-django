# aws_ec2/tests/test_views.py
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch
import datetime

from aws_ec2.models import Booking, UserCredential


class RegisterViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('aws_ec2:register')
    
    def test_register_get(self):
        """Test GET request to register view"""
        response = self.client.get(self.register_url)
        
        # Check response status code and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'aws_ec2/register.html')
        
        # Check that form is in context
        self.assertIn('form', response.context)
    
    @patch('aws_ec2.views.BookingService.create_user_credentials')
    @patch('aws_ec2.views.EmailService.send_initial_confirmation')
    @patch('aws_ec2.views.BookingService.schedule_instance_creation')
    def test_register_post_success(self, mock_schedule, mock_email, mock_create_credentials):
        """Test successful POST request to register view"""
        # Set up mocks
        mock_credentials = [
            UserCredential(username='user1', password='pass1'),
            UserCredential(username='user2', password='pass2')
        ]
        mock_create_credentials.return_value = mock_credentials
        mock_schedule.return_value = True
        
        # Create form data with future date
        future_time = timezone.now() + datetime.timedelta(days=1)
        form_data = {
            'email': 'test@example.com',
            'booking_time': future_time.strftime('%Y-%m-%dT%H:%M'),
            'number_of_users': 2
        }
        
        # Submit the form
        response = self.client.post(self.register_url, form_data)
        
        # Check response status code and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'aws_ec2/registration_success.html')
        
        # Check context variables
        self.assertEqual(response.context['email'], 'test@example.com')
        self.assertEqual(response.context['credentials'], mock_credentials)
        
        # Check that a booking was created
        self.assertEqual(Booking.objects.count(), 1)
        booking = Booking.objects.first()
        self.assertEqual(booking.email, 'test@example.com')
        self.assertEqual(booking.number_of_users, 2)
        
        # Check that service methods were called
        mock_create_credentials.assert_called_once_with(booking, 2)
        mock_email.assert_called_once()
        mock_schedule.assert_called_once_with(booking)
    
    @patch('aws_ec2.views.BookingService.create_user_credentials')
    @patch('aws_ec2.views.EmailService.send_initial_confirmation')
    @patch('aws_ec2.views.BookingService.schedule_instance_creation')
    def test_register_post_scheduling_failure(self, mock_schedule, mock_email, mock_create_credentials):
        """Test POST request with scheduling failure"""
        # Set up mocks
        mock_credentials = [
            UserCredential(username='user1', password='pass1')
        ]
        mock_create_credentials.return_value = mock_credentials
        mock_schedule.return_value = False  # Scheduling fails
        
        # Create form data
        future_time = timezone.now() + datetime.timedelta(days=1)
        form_data = {
            'email': 'test@example.com',
            'booking_time': future_time.strftime('%Y-%m-%dT%H:%M'),
            'number_of_users': 1
        }
        
        # Submit the form
        response = self.client.post(self.register_url, form_data)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'aws_ec2/register.html')
        
        # Check for error in form
        self.assertFalse(response.context['form'].is_valid())
        self.assertTrue(response.context['form'].errors)
        
        # Check that service methods were called
        mock_create_credentials.assert_called_once()
        mock_email.assert_called_once()
        mock_schedule.assert_called_once()
    
    def test_register_post_invalid_form(self):
        """Test POST request with invalid form data"""
        # Create invalid form data (past date)
        past_time = timezone.now() - datetime.timedelta(hours=1)
        form_data = {
            'email': 'test@example.com',
            'booking_time': past_time.strftime('%Y-%m-%dT%H:%M'),
            'number_of_users': 2
        }
        
        # Submit the form
        response = self.client.post(self.register_url, form_data)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'aws_ec2/register.html')
        
        # Check for error in form
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('booking_time', response.context['form'].errors)
        
        # Check that no booking was created
        self.assertEqual(Booking.objects.count(), 0)
    
    @patch('aws_ec2.views.BookingService.create_user_credentials')
    def test_register_post_exception(self, mock_create_credentials):
        """Test POST request that raises an exception"""
        # Set up mock to raise exception
        mock_create_credentials.side_effect = Exception("Test error")
        
        # Create form data
        future_time = timezone.now() + datetime.timedelta(days=1)
        form_data = {
            'email': 'test@example.com',
            'booking_time': future_time.strftime('%Y-%m-%dT%H:%M'),
            'number_of_users': 2
        }
        
        # Submit the form
        response = self.client.post(self.register_url, form_data)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'aws_ec2/register.html')
        
        # Check for error in form
        self.assertFalse(response.context['form'].is_valid())
        self.assertTrue(response.context['form'].non_field_errors())
        
        # Check that no booking was created (should be rolled back due to transaction)
        self.assertEqual(Booking.objects.count(), 0)