# aws_ec2/tests/test_logging_service.py
from django.test import TestCase
from unittest.mock import patch, MagicMock
import logging

from aws_ec2.services.logging_service import LoggingService


class LoggingServiceTestCase(TestCase):
    @patch('aws_ec2.services.logging_service.LoggerSetup')
    def test_get_logger(self, mock_logger_setup):
        """Test that get_logger calls LoggerSetup with correct parameters"""
        # Set up mock
        mock_logger = MagicMock(spec=logging.Logger)
        mock_logger_setup.setup_logger.return_value = mock_logger
        
        # Call the method
        logger = LoggingService.get_logger("test_service")
        
        # Check the result
        self.assertEqual(logger, mock_logger)
        
        # Check that setup_logger was called with correct parameters
        mock_logger_setup.setup_logger.assert_called_once_with(
            name="test_service",
            log_dir="logs/booking",
            file_prefix="test_service"
        )