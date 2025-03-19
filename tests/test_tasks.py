# aws_ec2/tests/test_tasks.py
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
import datetime

from aws_ec2.models import Booking, UserCredential
from aws_ec2.tasks import create_scheduled_instances


class TasksTestCase(TestCase):
    def setUp(self):
        # Create a test booking
        self.booking = Booking.objects.create(
            email="test@example.com",
            booking_time=timezone.now() + datetime.timedelta(days=1),
            number_of_users=2
        )
        
        # Create test credentials
        self.credentials = [
            UserCredential.objects.create(
                booking=self.booking,
                username=f"user{i}",
                password=f"pass{i}"
            )
            for i in range(2)
        ]
    
    @patch('aws_ec2.tasks.BookingService.create_instances')
    @patch('aws_ec2.tasks.EmailService.send_instance_details')
    def test_create_scheduled_instances_success(self, mock_email, mock_create_instances):
        """Test successful execution of create_scheduled_instances task"""
        # Set up mock instance info
        mock_instance = MagicMock()
        mock_instance.id = "i-12345"
        mock_instance.public_dns_name = "ec2-test.amazonaws.com"
        
        instance_info = [
            (mock_instance, 
             [{"username": "user0", "password": "pass0"}, {"username": "user1", "password": "pass1"}],
             {"username": "pawsey", "password": "admin_pass"})
        ]
        mock_create_instances.return_value = instance_info
        
        # Call the task directly
        create_scheduled_instances(self.booking.id)
        
        # Check that the booking was updated
        self.booking.refresh_from_db()
        self.assertTrue(self.booking.ec2_instances_created)
        
        # Check that service methods were called correctly
        mock_create_instances.assert_called_once()
        mock_email.assert_called_once_with(self.booking.email, instance_info)
    
    @patch('aws_ec2.tasks.BookingService.create_instances')
    @patch('aws_ec2.tasks.EmailService.send_instance_details')
    @patch('aws_ec2.tasks.EmailService.send_creation_failure')
    def test_create_scheduled_instances_failure(self, mock_email_failure, mock_email_success, mock_create_instances):
        """Test failure handling in create_scheduled_instances task"""
        # Set up mock to return None (failure)
        mock_create_instances.return_value = None
        
        # Call the task directly
        create_scheduled_instances(self.booking.id)
        
        # Check that the booking was not updated
        self.booking.refresh_from_db()
        self.assertFalse(self.booking.ec2_instances_created)
        
        # Check that service methods were called correctly
        mock_create_instances.assert_called_once()
        mock_email_success.assert_not_called()
        mock_email_failure.assert_called_once_with(self.booking.email)
    
    @patch('aws_ec2.tasks.BookingService.create_instances')
    @patch('aws_ec2.tasks.EmailService.send_instance_details')
    def test_create_scheduled_instances_already_created(self, mock_email, mock_create_instances):
        """Test handling when instances are already created"""
        # Set booking as already having instances created
        self.booking.ec2_instances_created = True
        self.booking.save()
        
        # Call the task directly
        create_scheduled_instances(self.booking.id)
        
        # Check that service methods were not called
        mock_create_instances.assert_not_called()
        mock_email.assert_not_called()
    
    @patch('aws_ec2.tasks.BookingService.create_instances')
    def test_create_scheduled_instances_no_credentials(self, mock_create_instances):
        """Test handling when no credentials are found"""
        # Delete credentials
        UserCredential.objects.filter(booking=self.booking).delete()
        
        # Call the task directly
        create_scheduled_instances(self.booking.id)
        
        # Check that create_instances was not called
        mock_create_instances.assert_not_called()
    
    def test_create_scheduled_instances_invalid_booking(self):
        """Test handling when booking ID is invalid"""
        # Call the task with invalid booking ID
        create_scheduled_instances(999)
        
        # No assertions needed - task should handle the exception internally
    
    @patch('aws_ec2.tasks.BookingService.create_instances')
    def test_create_scheduled_instances_exception(self, mock_create_instances):
        """Test exception handling in task"""
        # Set up mock to raise exception
        mock_create_instances.side_effect = Exception("Test exception")
        
        # Call the task - should not raise exception
        create_scheduled_instances(self.booking.id)
        
        # Check that the booking was not updated
        self.booking.refresh_from_db()
        self.assertFalse(self.booking.ec2_instances_created)