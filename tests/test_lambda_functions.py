# aws_ec2/tests/test_lambda_functions.py
from django.test import TestCase
from unittest.mock import patch, MagicMock

from aws_ec2.lamdba_functions.stop_instance import lambda_handler as stop_handler
from aws_ec2.lamdba_functions.terminate_instance import lambda_handler as terminate_handler


class LambdaFunctionsTestCase(TestCase):
    def setUp(self):
        # Prepare test event
        self.event = {
            'instance_id': 'i-12345abcdef'
        }
        
        # Mock context
        self.context = MagicMock()
    
    @patch('aws_ec2.lamdba_functions.stop_instance.boto3')
    def test_stop_instance_running(self, mock_boto3):
        """Test stopping a running instance"""
        # Set up mocks
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        # Mock describe_instances response
        mock_client.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [{
                    'State': {'Name': 'running'}
                }]
            }]
        }
        
        # Mock stop_instances response
        mock_client.stop_instances.return_value = {'StoppingInstances': [{'InstanceId': 'i-12345abcdef'}]}
        
        # Call the handler
        response = stop_handler(self.event, self.context)
        
        # Check boto3 calls
        mock_boto3.client.assert_called_once_with('ec2')
        mock_client.describe_instances.assert_called_once_with(InstanceIds=['i-12345abcdef'])
        mock_client.stop_instances.assert_called_once_with(InstanceIds=['i-12345abcdef'])
        
        # Check response
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Successfully initiated shutdown', response['body'])
    
    @patch('aws_ec2.lamdba_functions.stop_instance.boto3')
    def test_stop_instance_not_running(self, mock_boto3):
        """Test stopping an instance that is not running"""
        # Set up mocks
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        # Mock describe_instances response for stopped instance
        mock_client.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [{
                    'State': {'Name': 'stopped'}
                }]
            }]
        }
        
        # Call the handler
        response = stop_handler(self.event, self.context)
        
        # Check boto3 calls
        mock_client.describe_instances.assert_called_once()
        mock_client.stop_instances.assert_not_called()  # Should not be called for already stopped instance
        
        # Check response
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('already in state', response['body'])
    
    @patch('aws_ec2.lamdba_functions.stop_instance.boto3')
    def test_stop_instance_error(self, mock_boto3):
        """Test error handling in stop instance handler"""
        # Set up mocks to raise exception
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.describe_instances.side_effect = Exception("API Error")
        
        # Call the handler and expect exception to be re-raised
        with self.assertRaises(Exception):
            stop_handler(self.event, self.context)
    
    @patch('aws_ec2.lamdba_functions.terminate_instance.boto3')
    def test_terminate_instance_not_terminated(self, mock_boto3):
        """Test terminating an instance that is not already terminated"""
        # Set up mocks
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        # Mock describe_instances response
        mock_client.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [{
                    'State': {'Name': 'running'}
                }]
            }]
        }
        
        # Mock terminate_instances response
        mock_client.terminate_instances.return_value = {'TerminatingInstances': [{'InstanceId': 'i-12345abcdef'}]}
        
        # Call the handler
        response = terminate_handler(self.event, self.context)
        
        # Check boto3 calls
        mock_boto3.client.assert_called_once_with('ec2')
        mock_client.describe_instances.assert_called_once_with(InstanceIds=['i-12345abcdef'])
        mock_client.terminate_instances.assert_called_once_with(InstanceIds=['i-12345abcdef'])
        
        # Check response
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Successfully initiated termination', response['body'])
    
    @patch('aws_ec2.lamdba_functions.terminate_instance.boto3')
    def test_terminate_instance_already_terminated(self, mock_boto3):
        """Test terminating an already terminated instance"""
        # Set up mocks
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        # Mock describe_instances response for terminated instance
        mock_client.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [{
                    'State': {'Name': 'terminated'}
                }]
            }]
        }
        
        # Call the handler
        response = terminate_handler(self.event, self.context)
        
        # Check boto3 calls
        mock_client.describe_instances.assert_called_once()
        mock_client.terminate_instances.assert_not_called()  # Should not be called for already terminated instance
        
        # Check response
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('already terminated', response['body'])