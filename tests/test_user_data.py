# aws_ec2/tests/test_user_data.py
from django.test import TestCase
from unittest.mock import patch, MagicMock

from aws_ec2.ec2_utils.user_data import UserDataGenerator


class UserDataGeneratorTestCase(TestCase):
    def setUp(self):
        # Create the generator
        self.generator = UserDataGenerator()
        
        # Test data
        self.admin_password = "admin123"
        self.users = [
            {"username": "user1", "password": "pass1"},
            {"username": "user2", "password": "pass2"}
        ]
        self.requirements_url = "https://example.com/requirements.txt"
    
    def test_generate_pawsey_admin_setup(self):
        """Test generation of admin setup commands"""
        setup_commands = self.generator.generate_pawsey_admin_setup(self.admin_password)
        
        # Check that commands contain required elements
        self.assertIn("useradd -m -s /bin/bash pawsey", setup_commands)
        self.assertIn(f"pawsey:{self.admin_password}", setup_commands)
        self.assertIn("usermod -aG sudo pawsey", setup_commands)
        self.assertIn("sudoers.d/pawsey", setup_commands)
    
    def test_generate_user_setup(self):
        """Test generation of user setup commands"""
        setup_commands = self.generator.generate_user_setup(self.users)
        
        # Check that commands contain required elements for each user
        for user in self.users:
            self.assertIn(f"useradd -m -s /bin/bash {user['username']}", setup_commands)
            self.assertIn(f"{user['username']}:{user['password']}", setup_commands)
            self.assertIn(f"usermod -aG jupyter {user['username']}", setup_commands)
            self.assertIn(f"tljh-config add-item auth.PAMAuthenticator.whitelist {user['username']}", setup_commands)
    
    def test_generate_verification_commands(self):
        """Test generation of verification commands"""
        verification_commands = self.generator.generate_verification_commands(self.users)
        
        # Check admin verification
        self.assertIn('if id "pawsey"', verification_commands)
        
        # Check user verification commands
        for user in self.users:
            self.assertIn(f'if id "{user["username"]}"', verification_commands)
    
    def test_generate_full_script(self):
        """Test generation of complete user data script"""
        # Setup mocks
        self.generator.generate_pawsey_admin_setup = MagicMock(return_value="# Pawsey setup commands")
        self.generator.generate_user_setup = MagicMock(return_value="# User setup commands")
        self.generator.generate_verification_commands = MagicMock(return_value="# Verification commands")
        
        # Generate script
        script = self.generator.generate_full_script(
            self.admin_password,
            self.users,
            self.requirements_url
        )
        
        # Check that the script includes required elements
        self.assertIn("#!/bin/bash", script)
        self.assertIn("# Pawsey setup commands", script)
        self.assertIn("# User setup commands", script)
        self.assertIn(self.requirements_url, script)
        self.assertIn("# Verification commands", script)
        
        # Check usernames
        self.assertIn("user1 user2", script)  # Space-separated list of usernames

        # Check mock calls
        self.generator.generate_pawsey_admin_setup.assert_called_once_with(self.admin_password)
        self.generator.generate_user_setup.assert_called_once_with(self.users)
        self.generator.generate_verification_commands.assert_called_once_with(self.users)

    def test_generate_full_script_integration(self):
        """Test full script generation with actual components (integration test)"""
        # Generate script with real components, not mocks
        script = self.generator.generate_full_script(
            self.admin_password,
            self.users,
            self.requirements_url
        )
        
        # Check basic structure
        self.assertIn("#!/bin/bash", script)
        self.assertIn("sudo apt-get update", script)
        
        # Check Pawsey admin setup
        self.assertIn("useradd -m -s /bin/bash pawsey", script)
        self.assertIn(f"pawsey:{self.admin_password}", script)
        
        # Check user setup
        for user in self.users:
            self.assertIn(f"{user['username']}:{user['password']}", script)
            
        # Check requirements URL
        self.assertIn(self.requirements_url, script)
        
        # Check verification
        self.assertIn("Verifying Pawsey admin user", script)
        self.assertIn("Verifying JupyterHub users", script)