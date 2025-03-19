# aws_ec2/tests/test_instance_manager.py
from django.test import TestCase
from unittest.mock import patch, MagicMock, call
import boto3
import logging
import pytz
from datetime import datetime, timedelta

from aws_ec2.ec2_utils.instance_manager import EC2InstanceManager


class EC2InstanceManagerTestCase(TestCase):
    def setUp(self):
        # Create mocks
        self.mock_ec2_resource = MagicMock()
        self.mock_sg_manager = MagicMock()
        self.mock_logger = MagicMock(spec=logging.Logger)
        
        # Create the instance manager
        self.instance_manager = EC2InstanceManager(
            self.mock_ec2_resource,
            self.mock_sg_manager,
            self.mock_logger
        )
        
        # Override timestamp for predictable testing
        self.instance_manager.timestamp = "20241209123456"
        
        # Mock the boto3 clients
        self.instance_manager.events_client = MagicMock()
        self.instance_manager.lambda_client = MagicMock()
    
    @patch('aws_ec2.ec2_utils.instance_manager.datetime')
    @patch('aws_ec2.ec2_utils.instance_manager.boto3')
    def test_schedule_instance_shutdown_success(self, mock_boto3, mock_datetime):
        """Test successful scheduling of instance shutdown"""
        # Set up mocks
        mock_now = datetime.now(pytz.timezone('Australia/Perth'))
        mock_datetime.now.return_value = mock_now
        
        # Mock STS get_caller_identity
        mock_sts_client = MagicMock()
        mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}
        mock_boto3.client.return_value = mock_sts_client
        
        # Set up region for testing
        self.mock_ec2_resource.meta.client.meta.region_name = "ap-southeast-2"
        
        # Call the method
        result = self.instance_manager.schedule_instance_shutdown("i-12345", 60)
        
        # Check EventBridge rule creation
        self.instance_manager.events_client.put_rule.assert_called_once()
        rule_name = self.instance_manager.events_client.put_rule.call_args[1]['Name']
        self.assertIn("shutdown-i-12345", rule_name)
        
        # Check Lambda permission
        self.instance_manager.lambda_client.add_permission.assert_called_once()
        
        # Check EventBridge target
        self.instance_manager.events_client.put_targets.assert_called_once()
        target_args = self.instance_manager.events_client.put_targets.call_args[1]
        self.assertEqual(target_args['Rule'], rule_name)
        self.assertEqual(len(target_args['Targets']), 1)
        self.assertEqual(target_args['Targets'][0]['Id'], "ShutdownTarget-i-12345")
        
        # Check result
        self.assertTrue(result)
    
    @patch('aws_ec2.ec2_utils.instance_manager.boto3')
    def test_schedule_instance_shutdown_error(self, mock_boto3):
        """Test error handling when scheduling instance shutdown"""
        # Set up the events_client to raise an exception
        self.instance_manager.events_client.put_rule.side_effect = Exception("API Error")
        
        # Call the method
        result = self.instance_manager.schedule_instance_shutdown("i-12345", 60)
        
        # Check error logging
        self.mock_logger.error.assert_called_once()
        
        # Check result
        self.assertFalse(result)
    
    def test_create_instances_success(self):
        """Test successful creation of EC2 instances"""
        # Set up the mock EC2 resource
        mock_instance = MagicMock()
        mock_instance.id = "i-12345"
        self.mock_ec2_resource.create_instances.return_value = [mock_instance]
        
        # Set up mock for schedule_instance_shutdown
        self.instance_manager.schedule_instance_shutdown = MagicMock(return_value=True)
        
        # Test data
        instance_configs = [{
            'user_data': 'echo "Test"',
            'users': [{'username': 'testuser', 'password': 'testpass'}],
            'admin_credentials': {'username': 'admin', 'password': 'adminpass'}
        }]
        
        # Call the method
        instances = self.instance_manager.create_instances(
            instance_configs,
            'ami-12345',
            't2.micro',
            'test-key',
            'sg-12345'
        )
        
        # Check EC2 instance creation
        self.mock_ec2_resource.create_instances.assert_called_once()
        create_args = self.mock_ec2_resource.create_instances.call_args[1]
        self.assertEqual(create_args['ImageId'], 'ami-12345')
        self.assertEqual(create_args['InstanceType'], 't2.micro')
        self.assertEqual(create_args['KeyName'], 'test-key')
        self.assertEqual(create_args['SecurityGroupIds'], ['sg-12345'])
        
        # Check schedule_instance_shutdown call
        self.instance_manager.schedule_instance_shutdown.assert_called_once_with(mock_instance.id)
        
        # Check result
        self.assertEqual(len(instances), 1)
        instance, users, admin_creds = instances[0]
        self.assertEqual(instance, mock_instance)
        self.assertEqual(users, [{'username': 'testuser', 'password': 'testpass'}])
        self.assertEqual(admin_creds, {'username': 'admin', 'password': 'adminpass'})
    
    def test_create_instances_error(self):
        """Test error handling when creating EC2 instances"""
        # Set up the mock EC2 resource to raise an exception
        self.mock_ec2_resource.create_instances.side_effect = Exception("EC2 API Error")
        
        # Test data
        instance_configs = [{
            'user_data': 'echo "Test"',
            'users': [{'username': 'testuser', 'password': 'testpass'}],
            'admin_credentials': {'username': 'admin', 'password': 'adminpass'}
        }]
        
        # Call the method and expect exception
        with self.assertRaises(Exception):
            self.instance_manager.create_instances(
                instance_configs,
                'ami-12345',
                't2.micro',
                'test-key',
                'sg-12345'
            )
    
    @patch('aws_ec2.ec2_utils.instance_manager.time')
    def test_wait_for_instances_success(self, mock_time):
        """Test successful waiting for instances"""
        # Mock instances
        mock_instance1 = MagicMock()
        mock_instance2 = MagicMock()
        
        instances = [
            (mock_instance1, [], {}),
            (mock_instance2, [], {})
        ]
        
        # Call the method
        result = self.instance_manager.wait_for_instances(instances)
        
        # Check instance wait calls
        mock_instance1.wait_until_running.assert_called_once()
        mock_instance2.wait_until_running.assert_called_once()
        
        # Check reload calls
        mock_instance1.reload.assert_called_once()
        mock_instance2.reload.assert_called_once()
        
        # Check time.sleep for TLJH installation
        mock_time.sleep.assert_called_once_with(180)
        
        # Check result
        self.assertTrue(result)
    
    @patch('aws_ec2.ec2_utils.instance_manager.time')
    def test_wait_for_instances_error(self, mock_time):
        """Test error handling when waiting for instances"""
        # Mock instance that raises error
        mock_instance = MagicMock()
        mock_instance.wait_until_running.side_effect = Exception("Timeout")
        
        instances = [(mock_instance, [], {})]
        
        # Call the method
        result = self.instance_manager.wait_for_instances(instances)
        
        # Check error logging
        self.mock_logger.error.assert_called_once()
        
        # Check result
        self.assertFalse(result)