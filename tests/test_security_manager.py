# aws_ec2/tests/test_security_manager.py
from django.test import TestCase
from unittest.mock import patch, MagicMock, call
import logging
from botocore.exceptions import ClientError

from aws_ec2.ec2_utils.security import SecurityGroupManager


class SecurityGroupManagerTestCase(TestCase):
    def setUp(self):
        # Create mocks
        self.mock_ec2_resource = MagicMock()
        self.mock_logger = MagicMock(spec=logging.Logger)
        
        # Create the security group manager
        self.sg_manager = SecurityGroupManager(
            self.mock_ec2_resource,
            self.mock_logger
        )
    
    def test_create_or_get_security_group_existing(self):
        """Test getting an existing security group"""
        # Set up mock security group
        mock_sg = MagicMock()
        mock_sg.group_name = 'test-sg'
        mock_sg.id = 'sg-12345'
        
        # Set up security groups collection
        mock_sg_collection = MagicMock()
        mock_sg_collection.all.return_value = [mock_sg]
        self.mock_ec2_resource.security_groups = mock_sg_collection
        
        # Call the method
        sg_id = self.sg_manager.create_or_get_security_group('test-sg', 'Test security group')
        
        # Check that the existing group was found
        self.assertEqual(sg_id, 'sg-12345')
        
        # Check that create_security_group was not called
        self.mock_ec2_resource.create_security_group.assert_not_called()
    
    def test_create_or_get_security_group_new(self):
        """Test creating a new security group"""
        # Set up empty security groups collection
        mock_sg_collection = MagicMock()
        mock_sg_collection.all.return_value = []
        self.mock_ec2_resource.security_groups = mock_sg_collection
        
        # Set up create_security_group mock
        mock_sg = MagicMock()
        mock_sg.id = 'sg-67890'
        self.mock_ec2_resource.create_security_group.return_value = mock_sg
        
        # Call the method
        sg_id = self.sg_manager.create_or_get_security_group('new-sg', 'New security group')
        
        # Check that create_security_group was called
        self.mock_ec2_resource.create_security_group.assert_called_once_with(
            GroupName='new-sg',
            Description='New security group'
        )
        
        # Check the returned ID
        self.assertEqual(sg_id, 'sg-67890')
    
    def test_create_or_get_security_group_error(self):
        """Test error handling when creating/getting security group"""
        # Set up security groups collection to raise an exception
        self.mock_ec2_resource.security_groups.all.side_effect = ClientError(
            {'Error': {'Code': 'InternalError', 'Message': 'API error'}},
            'operation'
        )
        
        # Call the method
        sg_id = self.sg_manager.create_or_get_security_group('test-sg', 'Test security group')
        
        # Check error logging
        self.mock_logger.error.assert_called_once()
        
        # Check that None was returned
        self.assertIsNone(sg_id)
    
    def test_authorize_ingress_rule_success(self):
        """Test successful authorization of ingress rule"""
        # Create mock security group
        mock_sg = MagicMock()
        
        # Call the method
        result = self.sg_manager.authorize_ingress_rule(
            mock_sg,
            'tcp',
            22,
            22,
            '0.0.0.0/0'
        )
        
        # Check security group call
        mock_sg.authorize_ingress.assert_called_once_with(
            IpProtocol='tcp',
            FromPort=22,
            ToPort=22,
            CidrIp='0.0.0.0/0'
        )
        
        # Check result
        self.assertTrue(result)
    
    def test_authorize_ingress_rule_duplicate(self):
        """Test handling duplicate ingress rule"""
        # Create mock security group with duplicate error
        mock_sg = MagicMock()
        mock_sg.authorize_ingress.side_effect = ClientError(
            {'Error': {'Code': 'InvalidPermission.Duplicate', 'Message': 'Rule already exists'}},
            'authorize_ingress'
        )
        
        # Call the method
        result = self.sg_manager.authorize_ingress_rule(
            mock_sg,
            'tcp',
            22,
            22,
            '0.0.0.0/0'
        )
        
        # Check result - should still be True for duplicates
        self.assertTrue(result)
    
    def test_authorize_ingress_rule_error(self):
        """Test error handling for ingress rule authorization"""
        # Create mock security group with error
        mock_sg = MagicMock()
        mock_sg.authorize_ingress.side_effect = ClientError(
            {'Error': {'Code': 'InvalidGroup', 'Message': 'Security group not found'}},
            'authorize_ingress'
        )
        
        # Call the method
        result = self.sg_manager.authorize_ingress_rule(
            mock_sg,
            'tcp',
            22,
            22,
            '0.0.0.0/0'
        )
        
        # Check error logging
        self.mock_logger.error.assert_called_once()
        
        # Check result
        self.assertFalse(result)
    
    def test_setup_jupyter_security_rules(self):
        """Test setting up all Jupyter security rules"""
        # Create mock security group
        mock_sg = MagicMock()
        
        # Mock authorize_ingress_rule to track calls
        self.sg_manager.authorize_ingress_rule = MagicMock(return_value=True)
        
        # Call the method
        result = self.sg_manager.setup_jupyter_security_rules(mock_sg)
        
        # Check authorize_ingress_rule calls
        expected_calls = [
            call(mock_sg, 'tcp', 22, 22, '0.0.0.0/0'),
            call(mock_sg, 'tcp', 80, 80, '0.0.0.0/0'),
            call(mock_sg, 'tcp', 443, 443, '0.0.0.0/0')
        ]
        self.sg_manager.authorize_ingress_rule.assert_has_calls(expected_calls)
        self.assertEqual(self.sg_manager.authorize_ingress_rule.call_count, 3)
        
        # Check result
        self.assertTrue(result)
    
    def test_setup_jupyter_security_rules_failure(self):
        """Test failure when setting up security rules"""
        # Create mock security group
        mock_sg = MagicMock()
        
        # Mock authorize_ingress_rule to fail on second rule
        call_results = [True, False, True]
        self.sg_manager.authorize_ingress_rule = MagicMock(side_effect=call_results)
        
        # Call the method
        result = self.sg_manager.setup_jupyter_security_rules(mock_sg)
        
        # Check result - should be False because one rule failed
        self.assertFalse(result)