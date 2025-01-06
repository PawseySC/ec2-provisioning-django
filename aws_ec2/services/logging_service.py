from ..ec2_utils.logging_config import LoggerSetup

class LoggingService:
    """Centralized logging service"""
    
    @staticmethod
    def get_logger(name: str):
        return LoggerSetup.setup_logger(
            name=name,
            log_dir="logs/booking",
            file_prefix=name
        )
