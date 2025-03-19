# aws_ec2/tests/test_email_service.py
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch
import datetime

from aws_ec2.models import Booking, UserCredential, EC2Instance
from aws_ec2.services.email_service import EmailService


class EmailServiceTestCase(TestCase):
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
        
        # Create a test instance
        self.instance = EC2Instance.objects.create(
            booking=self.booking,
            instance_id="i-12345",
            public_dns="ec2-test.amazonaws.com"
        )
    
    @patch('aws_ec2.services.email_service.send_mail')
    def test_send_initial_confirmation(self, mock_send_mail):
        """Test that initial confirmation email is sent correctly"""
        EmailService.send_initial_confirmation(
            self.booking.email,
            self.booking.booking_time,
            self.credentials
        )
        
        # Check that send_mail was called once
        mock_send_mail.assert_called_once()
        
        # Check the arguments
        args, kwargs = mock_send_mail.call_args
        subject, message, from_email, recipients = args
        
        self.assertEqual(subject, "Booking Confirmation")
        self.assertEqual(recipients, [self.booking.email])
        
        # Check message content
        self.assertIn(self.booking.email, message)
        for cred in self.credentials:
            self.assertIn(cred.username, message)
            self.assertIn(cred.password, message)
    
    @patch('aws_ec2.services.email_service.send_mail')
    def test_send_instance_details(self, mock_send_mail):
        """Test that instance details email is sent correctly"""
        # Prepare instance info structure
        instance_info = [
            (
                self.instance,
                [{"username": "user0"}, {"username": "user1"}],
                {"username": "pawsey", "password": "admin_pass"}
            )
        ]
        
        # Call the method
        EmailService.send_instance_details(
            self.booking.email,
            instance_info
        )
        
        # Check that send_mail was called once
        mock_send_mail.assert_called_once()
        
        # Check the arguments
        args, kwargs = mock_send_mail.call_args
        subject, message, from_email, recipients = args
        
        self.assertEqual(subject, "JupyterHub Access Information")
        self.assertEqual(recipients, [self.booking.email])
        
        # Check message content
        self.assertIn(self.instance.public_dns, message)
        self.assertIn("user0", message)
        self.assertIn("user1", message)
        self.assertIn("pawsey", message)
        self.assertIn("admin_pass", message)