# EC2 Booking and Management System

![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![Django](https://img.shields.io/badge/django-5.1.3-green.svg)
![Celery](https://img.shields.io/badge/celery-5.4.0-orange.svg)
![AWS](https://img.shields.io/badge/aws-boto3-yellow.svg)

A comprehensive Django-based web application for booking and managing AWS EC2 instances with JupyterHub automation for educational workshops and hackathons.

## Features

- **User-friendly Booking Interface**: Simple form for users to schedule EC2 resources
- **Automated EC2 Provisioning**: On-demand creation of JupyterHub instances
- **Credential Management**: Automatic generation and delivery of user credentials
- **Email Notifications**: Booking confirmations and instance access details
- **Scheduled Tasks**: Time-based instance provisioning and shutdown
- **AWS Integration**: Complete EC2 lifecycle management
- **Security**: Proper security group configuration and credential handling

## Table of Contents

- [System Architecture](#-system-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Development](#-development)
- [Deployment](#-deployment)
- [Docker](#-docker)
- [Contributing](#-contributing)
- [License](#-license)

## System Architecture

The system is built using a modular architecture with the following components:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   Web Frontend  │────▶│  Django Backend │────▶│    AWS EC2      │
│                 │     │                 │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │                 │
                        │  Celery Tasks   │
                        │                 │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │                 │
                        │  Email Service  │
                        │                 │
                        └─────────────────┘
```

### Key Components:

- **Web Frontend**: User interface for registration and booking management
- **Django Backend**: Core application logic and data management
- **Celery Tasks**: Background jobs for scheduled provisioning and cleanup
- **AWS EC2 Integration**: Management of EC2 instances and security groups
- **Email Service**: Communication with users about bookings and resources

## Installation

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Redis 7+ (for Celery task queue)
- AWS Account with appropriate permissions
- Docker and Docker Compose (optional)

### Local Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ec2-booking-system
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run database migrations:
   ```bash
   python manage.py migrate
   ```

6. Start the development server:
   ```bash
   python manage.py runserver
   ```

7. In a separate terminal, start Celery worker:
   ```bash
   celery -A booking worker -l info
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Django settings
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database settings
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432

# AWS settings
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_DEFAULT_REGION=ap-southeast-2

# EC2 configuration
AWS_INSTANCE_TYPE=t3.micro
AWS_AMI_ID=ami-0892a9c01908fafd1
AWS_KEY_NAME=aws_00

# JupyterHub settings
JUPYTER_REQUIREMENTS_URL=https://raw.githubusercontent.com/PawseySC/quantum-computing-hackathon/main/python/requirements.txt
JUPYTER_ADMIN_USERNAME=pawsey
JUPYTER_USERS_PER_INSTANCE=2

# Email settings
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password

# Celery settings
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
TIME_ZONE=Australia/Perth
```

### AWS IAM Permissions

The AWS user associated with the access key needs the following permissions:

- `ec2:RunInstances`
- `ec2:DescribeInstances`
- `ec2:TerminateInstances`
- `ec2:StopInstances`
- `ec2:CreateSecurityGroup`
- `ec2:AuthorizeSecurityGroupIngress`
- `ec2:DescribeSecurityGroups`
- `events:PutRule`
- `events:PutTargets`
- `lambda:AddPermission`
- `lambda:InvokeFunction`

## Usage

### Booking an EC2 Instance

1. Access the booking registration form at `http://localhost:8000/booking/register/`
2. Enter your email address, desired booking time, and the number of users
3. Submit the form to receive an email with user credentials
4. At the scheduled time, instances will be provisioned automatically
5. You'll receive a second email with instance access details once provisioning is complete

### Administration

Access the Django admin interface at `http://localhost:8000/admin/` to:

- View and manage bookings
- Check instance statuses
- Generate reports

## Development

### Project Structure

```
ec2-booking-system/
├── aws_ec2/                 # Main application
│   ├── ec2_utils/           # AWS EC2 utilities
│   ├── services/            # Service layer
│   ├── templates/           # HTML templates
│   ├── lambda_functions/    # AWS Lambda handlers
│   ├── management/          # Django management commands
│   ├── migrations/          # Database migrations
│   └── tests/               # Test suite
├── booking/                 # Project configuration
├── logs/                    # Log files
├── .env                     # Environment variables
├── docker-compose.yml       # Docker configuration
└── requirements.txt         # Python dependencies
```

## Deployment

### Production Environment Setup

For production deployment, adjust the following settings:

1. Set `DEBUG=False` in `.env`
2. Configure proper `ALLOWED_HOSTS`
3. Set up a production-grade database
4. Use a reverse proxy (Nginx/Apache)
5. Configure proper SSL certificates

### Deploying with WSGI

1. Install Gunicorn:
   ```bash
   pip install gunicorn
   ```

2. Run with Gunicorn:
   ```bash
   gunicorn booking.wsgi:application --bind 0.0.0.0:8000
   ```

3. Set up Supervisor to manage processes:
   ```
   [program:ec2booking]
   command=/path/to/venv/bin/gunicorn booking.wsgi:application --bind 0.0.0.0:8000
   directory=/path/to/project
   user=www-data
   autostart=true
   autorestart=true
   redirect_stderr=true
   stdout_logfile=/var/log/ec2booking.log
   ```

## Docker

The application can be run using Docker and Docker Compose for easier deployment.

### Starting with Docker Compose

```bash
docker-compose up --build
```

This will start the following services:
- Web application (Django)
- PostgreSQL database
- Redis for Celery
- Nginx as a reverse proxy

### Accessing the Application

- Web interface: `http://localhost:80/booking/register/`
- Admin interface: `http://localhost:80/admin/`

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run tests (`python manage.py test`)
5. Commit changes (`git commit -m 'Add some feature'`)
6. Push to the branch (`git push origin feature/your-feature`)
7. Create a Pull Request

Please make sure your code passes all tests and follows the project's coding style.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
