# aws_ec2/tests/test_logging_config.py
from django.test import TestCase
from unittest.mock import patch, MagicMock
import logging
import os

from aws_ec2.ec2_utils.logging_config import LoggerSetup


class LoggerSetupTestCase(TestCase):
    @patch('aws_ec2.ec2_utils.logging_config.os.makedirs')
    @patch('aws_ec2.ec2_utils.logging_config.os.path.exists')
    @patch('aws_ec2.ec2_utils.logging_config.logging')
    def test_setup_logger_creates_directory(self, mock_logging, mock_exists, mock_makedirs):
        """Test that setup_logger creates log directory if it doesn't exist"""
        # Set up mocks
        mock_exists.return_value = False
        mock_logger = MagicMock(spec=logging.Logger)
        mock_logging.getLogger.return_value = mock_logger
        
        # Call the method
        logger = LoggerSetup.setup_logger("test_logger", log_dir="test_logs")
        
        # Check that directory was created
        mock_exists.assert_called_once_with("test_logs")
        mock_makedirs.assert_called_once_with("test_logs")
    
    @patch('aws_ec2.ec2_utils.logging_config.os.path.exists')
    @patch('aws_ec2.ec2_utils.logging_config.logging')
    def test_setup_logger_with_existing_directory(self, mock_logging, mock_exists):
        """Test setup_logger with existing log directory"""
        # Set up mocks
        mock_exists.return_value = True
        mock_logger = MagicMock(spec=logging.Logger)
        mock_logging.getLogger.return_value = mock_logger
        
        # Call the method
        logger = LoggerSetup.setup_logger("test_logger")
        
        # Check that directory existence was checked but not created
        mock_exists.assert_called_once()
        
        # Check logger configuration
        mock_logging.getLogger.assert_called_once_with("test_logger")
        mock_logger.setLevel.assert_called_once_with(logging.DEBUG)
        
        # Check handlers were added
        self.assertEqual(mock_logger.addHandler.call_count, 2)  # File and console handlers
    
    @patch('aws_ec2.ec2_utils.logging_config.os.path.exists')
    @patch('aws_ec2.ec2_utils.logging_config.logging')
    def test_setup_logger_without_console(self, mock_logging, mock_exists):
        """Test setup_logger without console output"""
        # Set up mocks
        mock_exists.return_value = True
        mock_logger = MagicMock(spec=logging.Logger)
        mock_logging.getLogger.return_value = mock_logger
        
        # Call the method with console_output=False
        logger = LoggerSetup.setup_logger("test_logger", console_output=False)
        
        # Check that only one handler (file) was added
        self.assertEqual(mock_logger.addHandler.call_count, 1)
    
    @patch('aws_ec2.ec2_utils.logging_config.os.path.exists')
    @patch('aws_ec2.ec2_utils.logging_config.logging')
    @patch('aws_ec2.ec2_utils.logging_config.datetime')
    def test_setup_logger_file_path(self, mock_datetime, mock_logging, mock_exists):
        """Test that setup_logger uses correct file path"""
        # Set up mocks
        mock_exists.return_value = True
        mock_logger = MagicMock(spec=logging.Logger)
        mock_logging.getLogger.return_value = mock_logger
        mock_datetime.now.return_value.strftime.return_value = "20241210"
        
        # Capture the file handler creation
        mock_file_handler = MagicMock()
        mock_logging.FileHandler.return_value = mock_file_handler
        
        # Call the method
        logger = LoggerSetup.setup_logger("test_logger", log_dir="custom_logs", file_prefix="custom")
        
        # Check file handler creation
        mock_logging.FileHandler.assert_called_once_with("custom_logs/custom_20241210.log")
        
        # Check formatter was set
        mock_file_handler.setFormatter.assert_called_once()