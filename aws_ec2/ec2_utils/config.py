# ec2_utils/config.py
from typing import Dict, List
from dataclasses import dataclass
import os

@dataclass
class AWSConfig:
    """AWS-specific configuration settings"""
    REGION: str = 'ap-southeast-2'
    AMI_ID: str = 'ami-0892a9c01908fafd1'  # Ubuntu Server 20.04 LTS
    INSTANCE_TYPE: str = 't3.micro' #t2.large m5.large t2.micro t3.medium t3.micro 
    KEY_NAME: str = 'aws_00'

@dataclass
class SecurityGroupConfig:
    """Security group configuration settings"""
    NAME: str = 'TLJH-SG'
    DESCRIPTION: str = 'Security group for TLJH EC2 instances'
    
    # Default security group rules
    INGRESS_RULES: List[Dict] = None
    
    def __post_init__(self):
        self.INGRESS_RULES = [
            {
                'protocol': 'tcp',
                'from_port': 22,
                'to_port': 22,
                'cidr_ip': '0.0.0.0/0',
                'description': 'SSH access'
            },
            {
                'protocol': 'tcp',
                'from_port': 80,
                'to_port': 80,
                'cidr_ip': '0.0.0.0/0',
                'description': 'HTTP access'
            },
            {
                'protocol': 'tcp',
                'from_port': 443,
                'to_port': 443,
                'cidr_ip': '0.0.0.0/0',
                'description': 'HTTPS access'
            }
        ]

@dataclass
class JupyterConfig:
    """JupyterHub-specific configuration"""
    REQUIREMENTS_URL: str = "https://raw.githubusercontent.com/PawseySC/quantum-computing-hackathon/main/python/requirements.txt"
    ADMIN_USERNAME: str = "pawsey"
    DEFAULT_USERS_PER_INSTANCE: int = 2
    INSTALLATION_WAIT_TIME: int = 180  # seconds
    
    # JupyterHub server settings
    HUB_PORT: int = 8000
    SSL_ENABLED: bool = True
    
    # User environment settings
    USER_ENV_TYPE: str = "python3"
    INSTALL_EXTENSIONS: bool = True

@dataclass
class LoggingConfig:
    """Logging configuration settings"""
    LOG_DIR: str = "logs"
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    CONSOLE_LOG_ENABLED: bool = True
    FILE_LOG_ENABLED: bool = True
    LOG_FILE_PREFIX: str = "ec2"
    MAX_LOG_FILES: int = 30  # Number of log files to keep

@dataclass
class TaggingConfig:
    """Resource tagging configuration"""
    DEFAULT_TAGS: Dict = None
    
    def __post_init__(self):
        self.DEFAULT_TAGS = {
            'Environment': os.getenv('ENVIRONMENT', 'development'),
            'Project': 'quantum-computing-hackathon',
            'ManagedBy': 'ec2-utils'
        }

class Config:
    """Main configuration class that combines all config categories"""
    def __init__(self):
        self.aws = AWSConfig()
        self.security_group = SecurityGroupConfig()
        self.jupyter = JupyterConfig()
        self.logging = LoggingConfig()
        self.tagging = TaggingConfig()
        
        # Load environment-specific overrides
        self._load_environment_overrides()
    
    def _load_environment_overrides(self):
        """Load configuration overrides from environment variables"""
        env_map = {
            'AWS_REGION': (self.aws, 'REGION'),
            'AWS_AMI_ID': (self.aws, 'AMI_ID'),
            'AWS_INSTANCE_TYPE': (self.aws, 'INSTANCE_TYPE'),
            'AWS_KEY_NAME': (self.aws, 'KEY_NAME'),
            'SECURITY_GROUP_NAME': (self.security_group, 'NAME'),
            'JUPYTER_REQUIREMENTS_URL': (self.jupyter, 'REQUIREMENTS_URL'),
            'JUPYTER_ADMIN_USERNAME': (self.jupyter, 'ADMIN_USERNAME'),
            'JUPYTER_USERS_PER_INSTANCE': (self.jupyter, 'DEFAULT_USERS_PER_INSTANCE'),
            'LOG_LEVEL': (self.logging, 'LOG_LEVEL'),
            'LOG_DIR': (self.logging, 'LOG_DIR')
        }
        
        for env_var, (config_obj, attr_name) in env_map.items():
            if env_value := os.getenv(env_var):
                setattr(config_obj, attr_name, env_value)

    @property
    def instance_tags(self) -> Dict:
        """Get the complete set of tags for EC2 instances"""
        tags = self.tagging.DEFAULT_TAGS.copy()
        tags.update({
            'Service': 'JupyterHub',
            'CreatedAt': '${timestamp}'  # This will be replaced at runtime
        })
        return tags

# Create a global config instance
config = Config()

# Usage examples:
"""
from ec2_utils.config import config

# Access AWS configuration
region = config.aws.REGION
instance_type = config.aws.INSTANCE_TYPE

# Access security group configuration
sg_name = config.security_group.NAME
ingress_rules = config.security_group.INGRESS_RULES

# Access JupyterHub configuration
admin_user = config.jupyter.ADMIN_USERNAME
users_per_instance = config.jupyter.DEFAULT_USERS_PER_INSTANCE

# Access logging configuration
log_dir = config.logging.LOG_DIR
log_level = config.logging.LOG_LEVEL

# Access tagging configuration
tags = config.instance_tags
"""