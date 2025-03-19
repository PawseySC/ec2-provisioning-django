# aws_ec2/tests/conftest.py
"""
Pytest configuration file for AWS EC2 tests.

This file contains pytest fixtures that can be shared across multiple test modules.
"""
import pytest
from django.utils import timezone
import datetime
from unittest.mock import MagicMock

from aws_ec2.models import Booking, UserCredential, EC2Instance


@pytest.fixture
def sample_booking():
    """Create a sample booking for testing"""
    booking = Booking.objects.create(
        email="test@example.com",
        booking_time=timezone.now() + datetime.timedelta(days=1),
        number_of_users=2
    )
    return booking


@pytest.fixture
def sample_credentials(sample_booking):
    """Create sample user credentials for testing"""
    credentials = [
        UserCredential.objects.create(
            booking=sample_booking,
            username=f"user{i}",
            password=f"pass{i}"
        )
        for i in range(2)
    ]
    return credentials


@pytest.fixture
def sample_instance(sample_booking):
    """Create a sample EC2 instance for testing"""
    instance = EC2Instance.objects.create(
        booking=sample_booking,
        instance_id="i-12345abcdef",
        public_dns="ec2-test.amazonaws.com"
    )
    return instance


@pytest.fixture
def mock_ec2_resource():
    """Create a mock EC2 resource"""
    mock = MagicMock()
    
    # Set up common mock attributes and methods
    mock_instance = MagicMock()
    mock_instance.id = "i-12345abcdef"
    mock_instance.public_dns_name = "ec2-test.amazonaws.com"
    mock_instance.state = {'Name': 'running'}
    
    mock.create_instances.return_value = [mock_instance]
    
    # Set up security group mocks
    mock_sg = MagicMock()
    mock_sg.id = "sg-12345"
    mock_sg.group_name = "test-sg"
    
    mock_sg_collection = MagicMock()
    mock_sg_collection.all.return_value = [mock_sg]
    mock.security_groups = mock_sg_collection
    
    mock.SecurityGroup.return_value = mock_sg
    
    return mock


@pytest.fixture
def mock_boto3_client():
    """Create a mock boto3 client"""
    mock = MagicMock()
    
    # Set up common mock attributes and methods
    mock.describe_instances.return_value = {
        'Reservations': [{
            'Instances': [{
                'InstanceId': 'i-12345abcdef',
                'PublicDnsName': 'ec2-test.amazonaws.com',
                'State': {'Name': 'running'}
            }]
        }]
    }
    
    return mock