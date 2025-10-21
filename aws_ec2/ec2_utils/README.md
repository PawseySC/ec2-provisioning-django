# EC2 Utilities

This directory contains the core functionality for AWS EC2 instance provisioning and management.

## Table of Contents

- [Overview](#overview)
- [Components](#components)
- [Configuration](#configuration)
- [Usage](#usage)
- [Development](#development)
- [Testing](#testing)

## Overview

The EC2 utilities provide a modular system for creating, configuring, and managing EC2 instances with JupyterHub. These utilities handle:

- Security group creation and configuration
- Instance provisioning with appropriate AMIs
- User data script generation for JupyterHub setup
- Instance lifecycle management (start, stop, terminate)
- Scheduled shutdown management via EventBridge

## Components

### `config.py`

Centralized configuration system with environment variable support. Uses a hierarchical structure with these components:

- `AWSConfig`: AWS-specific settings (region, AMI, instance type)
- `SecurityGroupConfig`: Security group rules and configuration
- `JupyterConfig`: JupyterHub installation and user settings
- `LoggingConfig`: Logging directories and format settings
- `TaggingConfig`: Resource tagging strategy

**Usage:**
```python
from aws_ec2.ec2_utils.config import config

# Access configuration
region = config.aws.REGION
security_group_name = config.security_group.NAME
jupyter_admin = config.jupyter.ADMIN_USERNAME
```

### `instance_manager.py`

Handles the lifecycle of EC2 instances including:

- Instance creation with proper configuration
- Scheduled shutdown using EventBridge
- Waiting for instances to be in the proper state

**Key Methods:**
- `create_instances()`: Provisions EC2 instances with specified configurations
- `wait_for_instances()`: Waits for instances to be ready
- `schedule_instance_shutdown()`: Sets up automatic shutdown

### `security.py`

Manages security groups and network rules:

- Creates required security groups or reuses existing ones
- Configures proper ingress rules for JupyterHub access
- Handles rule validation and deduplication

**Key Methods:**
- `create_or_get_security_group()`: Creates or finds existing security group
- `authorize_ingress_rule()`: Sets up network access rules
- `setup_jupyter_security_rules()`: Configures all required JupyterHub rules

### `user_data.py`

Generates EC2 user data scripts for instance initialization:

- Shell scripts for system updates and dependencies
- JupyterHub installation and configuration
- User account creation and management
- Security setup and verification steps

**Key Methods:**
- `generate_full_script()`: Creates complete bootstrap script
- `generate_pawsey_admin_setup()`: Admin user configuration
- `generate_user_setup()`: Regular user account creation

### `main.py`

Orchestrates the EC2 provisioning process:

- Coordinates between security, instance, and user data components
- Handles error cases and provides simplified interface
- Entry point for EC2-related operations

**Key Methods:**
- `create_ec2_instances()`: Main method for creating instances with JupyterHub

### `logging_config.py`

Configures logging for the EC2 utilities:

- Sets up file and console loggers
- Manages log rotation and formatting
- Provides consistent logging interface

## Configuration

The EC2 utilities can be configured through environment variables or directly in code. Key configuration parameters include:

| Parameter | Environment Variable | Default | Description |
|-----------|----------------------|---------|-------------|
| AWS Region | `AWS_REGION` | ap-southeast-2 | AWS region for instance creation |
| AMI ID | `AWS_AMI_ID` | ami-0892a9c01908fafd1 | AMI for EC2 instances |
| Instance Type | `AWS_INSTANCE_TYPE` | t3.micro | EC2 instance type |
| Key Name | `AWS_KEY_NAME` | aws_00 | SSH key pair name |
| Security Group | `SECURITY_GROUP_NAME` | TLJH-SG | Security group name |
| Admin Username | `JUPYTER_ADMIN_USERNAME` | pawsey | JupyterHub admin username |
| Users Per Instance | `JUPYTER_USERS_PER_INSTANCE` | 2 | Number of users per instance |

## Usage

### Basic Usage

```python
from aws_ec2.ec2_utils.main import EC2ServiceManager
from aws_ec2.services.logging_service import LoggingService

# Get logger
logger = LoggingService.get_logger("my_service")

# Create service manager
ec2_service = EC2ServiceManager(logger)

# User credentials
credentials = [
    {"username": "user1", "password": "password1"},
    {"username": "user2", "password": "password2"}
]

# Create instances
instances = ec2_service.create_ec2_instances(credentials)

# Process results
for instance, users, admin_credentials in instances:
    print(f"Instance ID: {instance.id}")
    print(f"Public DNS: {instance.public_dns_name}")
    print(f"Admin credentials: {admin_credentials}")
    print(f"User credentials: {users}")
```

### Advanced Configuration

To customize EC2 instance creation:

```python
# Import the configuration
from aws_ec2.ec2_utils.config import config

# Override configuration settings
config.aws.INSTANCE_TYPE = 't2.large'
config.jupyter.DEFAULT_USERS_PER_INSTANCE = 4
config.jupyter.REQUIREMENTS_URL = 'https://example.com/custom-requirements.txt'

# Then create instances as usual
ec2_service = EC2ServiceManager(logger)
instances = ec2_service.create_ec2_instances(credentials)
```

## Development

### Adding New Instance Types

To add support for new EC2 instance types:

1. Update `AWSConfig` in `config.py`:
   ```python
   @dataclass
   class AWSConfig:
       """AWS-specific configuration settings"""
       REGION: str = 'ap-southeast-2'
       AMI_ID: str = 'ami-0892a9c01908fafd1'  # Ubuntu Server 20.04 LTS
       INSTANCE_TYPE: str = 't3.micro'
       KEY_NAME: str = 'aws_00'
       # Add new types to the comment for documentation
       # t2.large m5.large t2.micro t3.medium t3.micro g4dn.xlarge
   ```

2. Test the new instance types thoroughly

### Custom User Data Scripts

To modify the JupyterHub installation or add custom packages:

1. Update the base script template in `UserDataGenerator._get_base_script_template()`
2. Add or modify package installation commands
3. Update verification steps in `generate_verification_commands()`

### Security Group Rules

To add or modify security group rules:

1. Update `INGRESS_RULES` in `SecurityGroupConfig.__post_init__()`
2. Add new rules to `setup_jupyter_security_rules()` in `SecurityGroupManager`

## Testing

The EC2 utilities include comprehensive unit tests. To run the tests:

```bash
python manage.py test aws_ec2.tests.test_instance_manager
python manage.py test aws_ec2.tests.test_security_manager
python manage.py test aws_ec2.tests.test_user_data
python manage.py test aws_ec2.tests.test_ec2_service_manager
python manage.py test aws_ec2.tests.test_config
```

When developing new features, always add appropriate tests in the `aws_ec2/tests/` directory.