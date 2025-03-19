# aws_ec2/tests/test_booking_service.py
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
import datetime

from aws_ec2.models import Booking, UserCredential, EC2Instance
from aws_ec2.services.booking_service import BookingService


class BookingServiceTestCase(TestCase):
    def setUp(self):
        # Create a test booking
        self.booking = Booking.objects.create(
            email="test@example.com",
            booking_time=timezone.now() + datetime.timedelta(days=1),
            number_of_users=2
        )

    def test_create_user_credentials(self):
        """Test that user credentials are created correctly"""
        credentials = BookingService.create_user_credentials(self.booking, 3)
        
        # Check that 3 credentials were created
        self.assertEqual(len(credentials), 3)
        
        # Check that all credentials are associated with the booking
        for cred in credentials:
            self.assertEqual(cred.booking, self.booking)
            
        # Check that credentials are saved in the database
        db_credentials = UserCredential.objects.filter(booking=self.booking)
        self.assertEqual(db_credentials.count(), 3)
    
    @patch('aws_ec2.services.booking_service.EC2ServiceManager')
    def test_create_instances_success(self, mock_ec2_service_manager):
        """Test successful instance creation"""
        # Create mock user credentials
        credentials = [
            UserCredential.objects.create(
                booking=self.booking,
                username=f"user{i}",
                password=f"pass{i}"
            )
            for i in range(2)
        ]
        
        # Set up the mock EC2ServiceManager
        mock_instance = MagicMock()
        mock_instance.id = "i-12345"
        mock_instance.public_dns_name = "ec2-test.amazonaws.com"
        
        mock_manager_instance = mock_ec2_service_manager.return_value
        mock_manager_instance.create_ec2_instances.return_value = [
            (mock_instance, 
             [{"username": "user0", "password": "pass0"}, {"username": "user1", "password": "pass1"}],
             {"username": "pawsey", "password": "admin_pass"})
        ]
        
        # Call the method
        result = BookingService.create_instances(self.booking, credentials)
        
        # Verify that EC2ServiceManager was called correctly
        mock_manager_instance.create_ec2_instances.assert_called_once()
        
        # Check the result
        self.assertEqual(len(result), 1)
        instance, users, admin_creds = result[0]
        self.assertEqual(instance.instance_id, "i-12345")
        self.assertEqual(instance.public_dns, "ec2-test.amazonaws.com")
        
        # Check that the booking was updated
        self.booking.refresh_from_db()
        self.assertTrue(self.booking.ec2_instances_created)
        
        # Check that the instance was saved to the database
        db_instance = EC2Instance.objects.get(booking=self.booking)
        self.assertEqual(db_instance.instance_id, "i-12345")
    
    @patch('aws_ec2.services.booking_service.EC2ServiceManager')
    def test_create_instances_failure(self, mock_ec2_service_manager):
        """Test instance creation failure"""
        # Create mock user credentials
        credentials = [
            UserCredential.objects.create(
                booking=self.booking,
                username=f"user{i}",
                password=f"pass{i}"
            )
            for i in range(2)
        ]
        
        # Set up the mock EC2ServiceManager to return None (failure)
        mock_manager_instance = mock_ec2_service_manager.return_value
        mock_manager_instance.create_ec2_instances.return_value = None
        
        # Call the method
        result = BookingService.create_instances(self.booking, credentials)
        
        # Verify EC2ServiceManager was called
        mock_manager_instance.create_ec2_instances.assert_called_once()
        
        # Check that the result is None
        self.assertIsNone(result)
        
        # Check that the booking was not updated
        self.booking.refresh_from_db()
        self.assertFalse(self.booking.ec2_instances_created)
        
        # Check that no instances were saved to the database
        db_instances = EC2Instance.objects.filter(booking=self.booking)
        self.assertEqual(db_instances.count(), 0)
    
    @patch('aws_ec2.services.booking_service.create_scheduled_instances')
    def test_schedule_instance_creation_success(self, mock_task):
        """Test successful scheduling of instance creation"""
        # Call the method
        result = BookingService.schedule_instance_creation(self.booking)
        
        # Verify that the Celery task was called with the booking ID
        mock_task.apply_async.assert_called_once()
        args, kwargs = mock_task.apply_async.call_args
        self.assertEqual(args[0][0], self.booking.id)
        self.assertEqual(kwargs.get('eta'), self.booking.booking_time)
        
        # Check the result
        self.assertTrue(result)
    
    @patch('aws_ec2.services.booking_service.create_scheduled_instances')
    def test_schedule_instance_creation_past_time(self, mock_task):
        """Test scheduling with a past booking time"""
        # Create a booking with a past time
        past_booking = Booking.objects.create(
            email="past@example.com",
            booking_time=timezone.now() - datetime.timedelta(hours=1),
            number_of_users=1
        )
        
        # Call the method
        result = BookingService.schedule_instance_creation(past_booking)
        
        # Check that the task was not scheduled
        mock_task.apply_async.assert_not_called()
        
        # Check the result
        self.assertFalse(result)