# Services Layer

This directory contains the service layer components that encapsulate the application's business logic.

## Table of Contents

- [Overview](#overview)
- [Services](#services)
- [Usage](#usage)
- [Development](#development)
- [Testing](#testing)

## Overview

The services layer provides a clean separation between controllers (views) and the underlying business logic. It encapsulates complex operations such as:

- Booking management and user credential generation
- EC2 instance provisioning
- Email notifications
- Logging and monitoring

By using services, we keep the views and models clean and focused on their primary responsibilities.

## Services

### `booking_service.py`

Manages the booking process and user credential generation.

**Key Methods:**

- `create_user_credentials()`: Generates secure credentials for users
- `create_instances()`: Provisions EC2 instances for a booking
- `schedule_instance_creation()`: Schedules instances to be created at a specific time

**Example:**

```python
from aws_ec2.services.booking_service import BookingService
from aws_ec2.models import Booking

# Create a booking
booking = Booking.objects.get(id=1)

# Generate user credentials
credentials = BookingService.create_user_credentials(booking, 3)

# Create instances
instances = BookingService.create_instances(booking, credentials)

# Or schedule for later
BookingService.schedule_instance_creation(booking)
```

### `email_service.py`

Handles email composition and delivery to users.

**Key Methods:**

- `send_initial_confirmation()`: Sends booking confirmation with credentials
- `send_instance_details()`: Sends EC2 instance access information

**Example:**

```python
from aws_ec2.services.email_service import EmailService
from aws_ec2.models import Booking, UserCredential

# Get booking and credentials
booking = Booking.objects.get(id=1)
credentials = UserCredential.objects.filter(booking=booking)

# Send initial confirmation
EmailService.send_initial_confirmation(
    booking.email,
    booking.booking_time,
    list(credentials)
)

# Send instance details
instance_info = [
    (instance, users_list, admin_credentials)
    for instance in booking.ec2_instances.all()
]
EmailService.send_instance_details(booking.email, instance_info)
```

### `logging_service.py`

Provides consistent logging throughout the application.

**Key Methods:**

- `get_logger()`: Creates and configures a logger for a specific component

**Example:**

```python
from aws_ec2.services.logging_service import LoggingService

# Get a logger for a specific component
logger = LoggingService.get_logger("booking_view")

# Use the logger
logger.info("Processing booking request")
logger.debug("Request data: %s", request_data)
logger.error("Error creating booking: %s", str(error))
```

## Usage

### Handling Booking Requests

```python
def process_booking(email, booking_time, number_of_users):
    try:
        # Create booking record
        booking = Booking.objects.create(
            email=email,
            booking_time=booking_time,
            number_of_users=number_of_users
        )
        
        # Generate credentials
        credentials = BookingService.create_user_credentials(
            booking, 
            number_of_users
        )
        
        # Send confirmation email
        EmailService.send_initial_confirmation(
            email, 
            booking_time, 
            credentials
        )
        
        # Schedule instance creation
        BookingService.schedule_instance_creation(booking)
        
        return True, credentials
        
    except Exception as e:
        logger = LoggingService.get_logger("booking_process")
        logger.error(f"Booking failed: {str(e)}", exc_info=True)
        return False, None
```

### Creating Instances Immediately

```python
def create_instances_now(booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
        credentials = list(booking.user_credentials.all())
        
        # Create instances
        instance_info = BookingService.create_instances(booking, credentials)
        
        if instance_info:
            # Send email with instance details
            EmailService.send_instance_details(booking.email, instance_info)
            return True
        else:
            return False
            
    except Exception as e:
        logger = LoggingService.get_logger("instance_creation")
        logger.error(f"Instance creation failed: {str(e)}", exc_info=True)
        return False
```

## Development

### Adding a New Service

1. Create a new file in the `services` directory (e.g., `notification_service.py`)
2. Implement service methods as static methods in a class
3. Add appropriate logging
4. Add unit tests in `aws_ec2/tests/`

Example new service:

```python
# aws_ec2/services/notification_service.py
from .logging_service import LoggingService

logger = LoggingService.get_logger("notification_service")

class NotificationService:
    """Handles user notifications beyond email"""
    
    @staticmethod
    def send_sms_notification(phone_number, message):
        """Sends SMS notification to a user"""
        try:
            # Implement SMS sending logic
            logger.info(f"Sending SMS to {phone_number}")
            # ...implementation...
            return True
        except Exception as e:
            logger.error(f"SMS notification failed: {str(e)}", exc_info=True)
            return False
```

### Modifying Existing Services

When modifying existing services:

1. Maintain backward compatibility when possible
2. Update unit tests to cover new functionality
3. Use appropriate logging
4. Consider the impact on other components

## Testing

The services layer includes comprehensive unit tests. To run the tests:

```bash
# Test specific service
python manage.py test aws_ec2.tests.test_booking_service
python manage.py test aws_ec2.tests.test_email_service
python manage.py test aws_ec2.tests.test_logging_service

# Test all services
python manage.py test aws_ec2.tests
```

When developing new features or modifying existing services, always add or update tests to maintain code quality and prevent regressions.