# aws_ec2/tests/test_ec2_service_manager.py
from django.test import TestCase
from unittest.mock import patch, MagicMock
import logging

from aws_ec2.ec2_utils.main import EC2ServiceManager


class EC2ServiceManagerTestCase(TestCase):
    def setUp(self):
        # Create mock logger
        self.mock_logger = MagicMock(spec=logging.Logger)
        
        # Mock the boto3 resource
        patcher = patch('aws_ec2.ec2_utils.main.boto3')
        self.mock_boto3 = patcher.start()
        self.addCleanup(patcher.stop)
        
        self.mock_ec2_resource = MagicMock()
        self.mock_boto3.resource.return_value = self.mock_ec2_resource
        
        # Create mock security group manager
        patcher = patch('aws_ec2.ec2_utils.main.SecurityGroupManager')
        self.MockSecurityGroupManager = patcher.start()
        self.addCleanup(patcher.stop)
        
        self.mock_sg_manager = MagicMock()
        self.MockSecurityGroupManager.return_value = self.mock_sg_manager
        
        # Create mock instance manager
        patcher = patch('aws_ec2.ec2_utils.main.EC2InstanceManager')
        self.MockInstanceManager = patcher.start()
        self.addCleanup(patcher.stop)
        
        self.mock_instance_manager = MagicMock()
        self.MockInstanceManager.return_value = self.mock_instance_manager
        
        # Create mock user data generator
        patcher = patch('aws_ec2.ec2_utils.main.UserDataGenerator')
        self.MockUserDataGenerator = patcher.start()
        self.addCleanup(patcher.stop)
        
        self.mock_user_data_generator = MagicMock()
        self.MockUserDataGenerator.return_value = self.mock_user_data_generator
        
        # Set up EC2ServiceManager
        self.ec2_service = EC2ServiceManager(self.mock_logger)
        
        # Test data
        self.credentials = [
            {"username": "user1", "password": "pass1"},
            {"username": "user2", "password": "pass2"}
        ]
    
    def test_init(self):
        """Test initialization of EC2ServiceManager"""
        # Check boto3 resource creation
        self.mock_boto3.resource.assert_called_once_with('ec2', region_name='ap-southeast-2')
        
        # Check security group manager creation
        self.MockSecurityGroupManager.assert_called_once_with(
            self.mock_ec2_resource,
            self.mock_logger
        )
        
        # Check instance manager creation
        self.MockInstanceManager.assert_called_once_with(
            self.mock_ec2_resource,
            self.mock_sg_manager,
            self.mock_logger
        )
        
        # Check user data generator creation
        self.MockUserDataGenerator.assert_called_once()
    
    def test_create_ec2_instances_success(self):
        """Test successful creation of EC2 instances"""
        # Mock security group creation
        self.mock_sg_manager.create_or_get_security_group.return_value = 'sg-12345'
        
        # Mock security group object
        mock_sg = MagicMock()
        self.mock_ec2_resource.SecurityGroup.return_value = mock_sg
        
        # Mock security rules setup
        self.mock_sg_manager.setup_jupyter_security_rules.return_value = True
        
        # Mock user data generation
        self.mock_user_data_generator.generate_full_script.return_value = 'echo "User data script"'
        
        # Mock instance creation and waiting
        mock_instance = MagicMock()
        mock_instance.id = 'i-12345'
        mock_instance.public_dns_name = 'ec2-test.amazonaws.com'
        
        instance_result = [(mock_instance, self.credentials, {'username': 'pawsey', 'password': 'admin123'})]
        self.mock_instance_manager.create_instances.return_value = instance_result
        self.mock_instance_manager.wait_for_instances.return_value = True
        
        # Call the method
        result = self.ec2_service.create_ec2_instances(self.credentials)
        
        # Check security group creation
        self.mock_sg_manager.create_or_get_security_group.assert_called_once()
        
        # Check security rules setup
        self.mock_sg_manager.setup_jupyter_security_rules.assert_called_once_with(mock_sg)
        
        # Check user data generation
        self.mock_user_data_generator.generate_full_script.assert_called_once()
        
        # Check instance creation
        self.mock_instance_manager.create_instances.assert_called_once()
        
        # Check waiting for instances
        self.mock_instance_manager.wait_for_instances.assert_called_once_with(instance_result)
        
        # Check result
        self.assertEqual(result, instance_result)
    
    def test_create_ec2_instances_security_group_failure(self):
        """Test failure to create/get security group"""
        # Mock security group creation to fail
        self.mock_sg_manager.create_or_get_security_group.return_value = None
        
        # Call the method
        result = self.ec2_service.create_ec2_instances(self.credentials)
        
        # Check security group creation
        self.mock_sg_manager.create_or_get_security_group.assert_called_once()
        
        # Check that further steps were not called
        self.mock_user_data_generator.generate_full_script.assert_not_called()
        self.mock_instance_manager.create_instances.assert_not_called()
        
        # Check result
        self.assertIsNone(result)
    
    def test_create_ec2_instances_security_rules_failure(self):
        """Test failure to set up security rules"""
        # Mock security group creation
        self.mock_sg_manager.create_or_get_security_group.return_value = 'sg-12345'
        
        # Mock security group object
        mock_sg = MagicMock()
        self.mock_ec2_resource.SecurityGroup.return_value = mock_sg
        
        # Mock security rules setup to fail
        self.mock_sg_manager.setup_jupyter_security_rules.return_value = False
        
        # Call the method
        result = self.ec2_service.create_ec2_instances(self.credentials)
        
        # Check security group creation
        self.mock_sg_manager.create_or_get_security_group.assert_called_once()
        
        # Check security rules setup
        self.mock_sg_manager.setup_jupyter_security_rules.assert_called_once_with(mock_sg)
        
        # Check that further steps were not called
        self.mock_user_data_generator.generate_full_script.assert_not_called()
        self.mock_instance_manager.create_instances.assert_not_called()
        
        # Check result
        self.assertIsNone(result)
    
    def test_create_ec2_instances_user_data_error(self):
        """Test error during user data generation"""
        # Mock security group creation
        self.mock_sg_manager.create_or_get_security_group.return_value = 'sg-12345'
        
        # Mock security group object
        mock_sg = MagicMock()
        self.mock_ec2_resource.SecurityGroup.return_value = mock_sg
        
        # Mock security rules setup
        self.mock_sg_manager.setup_jupyter_security_rules.return_value = True
        
        # Mock user data generation to raise exception
        self.mock_user_data_generator.generate_full_script.side_effect = Exception("User data error")
        
        # Call the method
        result = self.ec2_service.create_ec2_instances(self.credentials)
        
        # Check security group creation and rules setup
        self.mock_sg_manager.create_or_get_security_group.assert_called_once()
        self.mock_sg_manager.setup_jupyter_security_rules.assert_called_once()
        
        # Check user data generation
        self.mock_user_data_generator.generate_full_script.assert_called_once()
        
        # Check that instance creation was not called
        self.mock_instance_manager.create_instances.assert_not_called()
        
        # Check result
        self.assertIsNone(result)
    
    def test_create_ec2_instances_create_failure(self):
        """Test failure during instance creation"""
        # Mock security group creation
        self.mock_sg_manager.create_or_get_security_group.return_value = 'sg-12345'
        
        # Mock security group object
        mock_sg = MagicMock()
        self.mock_ec2_resource.SecurityGroup.return_value = mock_sg
        
        # Mock security rules setup
        self.mock_sg_manager.setup_jupyter_security_rules.return_value = True
        
        # Mock user data generation
        self.mock_user_data_generator.generate_full_script.return_value = 'echo "User data script"'
        
        # Mock instance creation to fail
        self.mock_instance_manager.create_instances.side_effect = Exception("EC2 creation error")
        
        # Call the method
        result = self.ec2_service.create_ec2_instances(self.credentials)
        
        # Check that all steps were called up to instance creation
        self.mock_sg_manager.create_or_get_security_group.assert_called_once()
        self.mock_sg_manager.setup_jupyter_security_rules.assert_called_once()
        self.mock_user_data_generator.generate_full_script.assert_called_once()
        self.mock_instance_manager.create_instances.assert_called_once()
        
        # Check waiting was not called
        self.mock_instance_manager.wait_for_instances.assert_not_called()
        
        # Check result
        self.assertIsNone(result)
    
    def test_create_ec2_instances_wait_failure(self):
        """Test failure during waiting for instances"""
        # Mock security group creation
        self.mock_sg_manager.create_or_get_security_group.return_value = 'sg-12345'
        
        # Mock security group object
        mock_sg = MagicMock()
        self.mock_ec2_resource.SecurityGroup.return_value = mock_sg
        
        # Mock security rules setup
        self.mock_sg_manager.setup_jupyter_security_rules.return_value = True
        
        # Mock user data generation
        self.mock_user_data_generator.generate_full_script.return_value = 'echo "User data script"'
        
        # Mock instance creation
        mock_instance = MagicMock()
        instance_result = [(mock_instance, [], {})]
        self.mock_instance_manager.create_instances.return_value = instance_result
        
        # Mock waiting to fail
        self.mock_instance_manager.wait_for_instances.return_value = False
        
        # Call the method
        result = self.ec2_service.create_ec2_instances(self.credentials)
        
        # Check all steps were called
        self.mock_sg_manager.create_or_get_security_group.assert_called_once()
        self.mock_sg_manager.setup_jupyter_security_rules.assert_called_once()
        self.mock_user_data_generator.generate_full_script.assert_called_once()
        self.mock_instance_manager.create_instances.assert_called_once()
        self.mock_instance_manager.wait_for_instances.assert_called_once()
        
        # Check result
        self.assertIsNone(result)