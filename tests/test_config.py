# aws_ec2/tests/test_config.py
from django.test import TestCase
from unittest.mock import patch
import os

from aws_ec2.ec2_utils.config import Config, AWSConfig, SecurityGroupConfig, JupyterConfig


class ConfigTestCase(TestCase):
    def test_default_aws_config(self):
        """Test default AWS configuration values"""
        aws_config = AWSConfig()
        
        self.assertEqual(aws_config.REGION, 'ap-southeast-2')
        self.assertEqual(aws_config.AMI_ID, 'ami-0892a9c01908fafd1')
        self.assertEqual(aws_config.INSTANCE_TYPE, 't3.micro')
        self.assertEqual(aws_config.KEY_NAME, 'aws_00')
    
    def test_security_group_config(self):
        """Test security group configuration"""
        sg_config = SecurityGroupConfig()
        
        self.assertEqual(sg_config.NAME, 'TLJH-SG')
        self.assertEqual(sg_config.DESCRIPTION, 'Security group for TLJH EC2 instances')
        
        # Check ingress rules
        self.assertEqual(len(sg_config.INGRESS_RULES), 3)
        
        # Check SSH rule
        ssh_rule = sg_config.INGRESS_RULES[0]
        self.assertEqual(ssh_rule['protocol'], 'tcp')
        self.assertEqual(ssh_rule['from_port'], 22)
        self.assertEqual(ssh_rule['to_port'], 22)
        self.assertEqual(ssh_rule['cidr_ip'], '0.0.0.0/0')
    
    def test_jupyter_config(self):
        """Test Jupyter configuration"""
        jupyter_config = JupyterConfig()
        
        self.assertTrue(jupyter_config.REQUIREMENTS_URL.startswith('https://'))
        self.assertEqual(jupyter_config.ADMIN_USERNAME, 'pawsey')
        self.assertEqual(jupyter_config.DEFAULT_USERS_PER_INSTANCE, 2)
        self.assertEqual(jupyter_config.INSTALLATION_WAIT_TIME, 180)
    
    @patch.dict(os.environ, {
        'AWS_REGION': 'us-west-2',
        'AWS_INSTANCE_TYPE': 't2.micro',
        'SECURITY_GROUP_NAME': 'custom-sg',
        'JUPYTER_ADMIN_USERNAME': 'admin',
        'JUPYTER_USERS_PER_INSTANCE': '3'
    })
    def test_environment_overrides(self):
        """Test that environment variables override default config"""
        config = Config()
        
        # Check AWS config overrides
        self.assertEqual(config.aws.REGION, 'us-west-2')
        self.assertEqual(config.aws.INSTANCE_TYPE, 't2.micro')
        
        # Check security group override
        self.assertEqual(config.security_group.NAME, 'custom-sg')
        
        # Check Jupyter config overrides
        self.assertEqual(config.jupyter.ADMIN_USERNAME, 'admin')
        self.assertEqual(config.jupyter.DEFAULT_USERS_PER_INSTANCE, '3')  # Note: would be string from env var
    
    def test_instance_tags(self):
        """Test instance tags property"""
        config = Config()
        tags = config.instance_tags
        
        # Check that tags include required keys
        self.assertIn('Environment', tags)
        self.assertIn('Project', tags)
        self.assertIn('ManagedBy', tags)
        self.assertIn('Service', tags)
        self.assertIn('CreatedAt', tags)
        
        # Check specific values
        self.assertEqual(tags['Service'], 'JupyterHub')