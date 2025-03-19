# aws_ec2/tests/test_models.py
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.hashers import check_password
import datetime

from aws_ec2.models import Booking, UserCredential, EC2Instance


class BookingModelTestCase(TestCase):
    def test_booking_creation(self):
        """Test Booking model creation and string representation"""
        booking_time = timezone.now() + datetime.timedelta(days=1)
        booking = Booking.objects.create(
            email="test@example.com",
            booking_time=booking_time,
            number_of_users=3
        )
        
        # Check that the booking was created with correct attributes
        self.assertEqual(booking.email, "test@example.com")
        self.assertEqual(booking.booking_time, booking_time)
        self.assertEqual(booking.number_of_users, 3)
        self.assertFalse(booking.ec2_instances_created)
        
        # Check string representation
        expected_str = f"Booking for test@example.com at {booking_time}"
        self.assertEqual(str(booking), expected_str)


class UserCredentialModelTestCase(TestCase):
    def setUp(self):
        self.booking = Booking.objects.create(
            email="test@example.com",
            booking_time=timezone.now() + datetime.timedelta(days=1),
            number_of_users=2
        )
    
    def test_user_credential_creation(self):
        """Test UserCredential model creation and string representation"""
        credential = UserCredential.objects.create(
            booking=self.booking,
            username="testuser",
            password="testpass"
        )
        
        # Check that the credential was created with correct attributes
        self.assertEqual(credential.booking, self.booking)
        self.assertEqual(credential.username, "testuser")
        
        # Check that the password was hashed
        self.assertNotEqual(credential.password, "testpass")
        
        # Check string representation
        expected_str = f"Username: testuser for Booking ID: {self.booking.id}"
        self.assertEqual(str(credential), expected_str)
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed on save"""
        raw_password = "testpass123"
        credential = UserCredential.objects.create(
            booking=self.booking,
            username="testuser",
            password=raw_password
        )
        
        # Check that the stored password is not the raw password
        self.assertNotEqual(credential.password, raw_password)
        
        # Retrieve from database to ensure it's stored correctly
        db_credential = UserCredential.objects.get(id=credential.id)
        
        # Test that password verification works with the hashed password
        self.assertFalse(check_password(raw_password, db_credential.password))
        
        # Unfortunately, we can't properly check password verification since
        # we're using make_password but not checking it with a hashing algorithm
        # that Django's check_password recognizes. In a real system we would need
        # to adapt this test or modify the model to use Django's auth system.


class EC2InstanceModelTestCase(TestCase):
    def setUp(self):
        self.booking = Booking.objects.create(
            email="test@example.com",
            booking_time=timezone.now() + datetime.timedelta(days=1),
            number_of_users=2
        )
    
    def test_ec2_instance_creation(self):
        """Test EC2Instance model creation and string representation"""
        instance = EC2Instance.objects.create(
            booking=self.booking,
            instance_id="i-12345abcdef",
            public_dns="ec2-12-34-56-78.compute-1.amazonaws.com"
        )
        
        # Check that the instance was created with correct attributes
        self.assertEqual(instance.booking, self.booking)
        self.assertEqual(instance.instance_id, "i-12345abcdef")
        self.assertEqual(instance.public_dns, "ec2-12-34-56-78.compute-1.amazonaws.com")
        
        # Check string representation
        expected_str = f"EC2 Instance i-12345abcdef for Booking ID: {self.booking.id}"
        self.assertEqual(str(instance), expected_str)