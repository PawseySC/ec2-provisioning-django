 
import logging
import os
from datetime import datetime
from typing import Optional

class LoggerSetup:
    @staticmethod
    def setup_logger(
        name: str,
        log_level: int = logging.DEBUG,
        log_dir: str = 'logs',
        file_prefix: str = 'ec2',
        console_output: bool = True
    ) -> logging.Logger:
        """
        Sets up a logger with both file and console handlers.
        
        Args:
            name: Logger name
            log_level: Logging level
            log_dir: Directory for log files
            file_prefix: Prefix for log file names
            console_output: Whether to output logs to console
            
        Returns:
            logging.Logger: Configured logger instance
        """
        # Create logs directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(log_level)

        # Clear any existing handlers
        logger.handlers = []

        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )

        # File handler
        file_path = os.path.join(
            log_dir,
            f"{file_prefix}_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Console handler
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

        return logger