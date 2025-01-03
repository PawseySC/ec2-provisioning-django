# booking/views.py
import secrets
from typing import List, Tuple, Optional
from django.shortcuts import render
from django.core.mail import send_mail
from django.db import transaction
from django.conf import settings

from .forms import BookingForm
from .models import Booking, UserCredential, EC2Instance
from .ec2_utils.main import EC2ServiceManager
from .ec2_utils.logging_config import LoggerSetup
from .ec2_utils.config import config

# Set up logging using the new LoggerSetup
logger = LoggerSetup.setup_logger(
    name="booking_views",
    log_dir="logs/booking",
    file_prefix="views"
)

class EmailService:
    """Handles email composition and sending"""
    
    @staticmethod
    def send_initial_confirmation(email: str, booking_time, credentials: List[UserCredential]) -> None:
        credentials_list = [
            f"Username: {cred.username}, Password: {cred.password}"
            for cred in credentials
        ]
        
        message = (
            f"Dear User,\n\n"
            f"Your booking has been successfully registered with the following details:\n\n"
            f"Email: {email}\n"
            f"Booking Time: {booking_time}\n\n"
            f"Generated User Credentials:\n{chr(10).join(credentials_list)}\n\n"
            f"JupyterHub URLs will be sent in a follow-up email once the instances are ready.\n\n"
            f"Please keep this information secure for your records.\n\n"
            f"Thank you for booking with us!"
        )
        
        send_mail(
            "Booking Confirmation",
            message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False
        )

    @staticmethod
    def send_instance_details(
        email: str,
        instance_info: List[Tuple[EC2Instance, List[dict], dict]]  # Updated type hint
    ) -> None:
        instance_details = []
        for instance, users, pawsey_credentials in instance_info:
            user_details = "\n".join([f"- {user['username']}" for user in users])
            instance_details.append(
                f"Instance URL: http://{instance.public_dns}\n"
                f"JupyterHub Users assigned to this instance:\n{user_details}\n"
                f"\nAdmin Access Credentials (for system administration only):\n"
                f"Username: {pawsey_credentials['username']}\n"
                f"Password: {pawsey_credentials['password']}\n"
            )
        
        message = (
            f"Dear User,\n\n"
            f"Your JupyterHub instances are now ready! Here are the access details:\n\n"
            f"{chr(10).join(instance_details)}\n"
            f"Important Notes:\n"
            f"1. It may take up to 5-10 minutes for the JupyterHub services to fully initialize.\n"
            f"2. Use the JupyterHub user credentials provided in the previous email to log in.\n"
            f"3. The Pawsey admin credentials are for system administration only and should be kept secure.\n"
            f"4. You may see a security warning about the certificate - this is expected for the demo environment.\n\n"
            f"If you experience any issues accessing the service, please wait a few minutes and try again.\n\n"
            f"Best regards,\n"
            f"Your JupyterHub Team"
        )
        
        send_mail(
            "JupyterHub Access Information",
            message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False
        )

class BookingService:
    """Handles booking and EC2 instance creation"""
    
    @staticmethod
    def create_user_credentials(booking: Booking, number_of_users: int) -> List[UserCredential]:
        credentials = [
            UserCredential(
                booking=booking,
                username=secrets.token_hex(8),
                password=secrets.token_hex(16)
            )
            for _ in range(number_of_users)
        ]
        UserCredential.objects.bulk_create(credentials)
        return credentials

    @staticmethod
    def create_instances(booking: Booking, credentials: List[UserCredential]) -> Optional[List[Tuple]]:
        try:
            # Log the type and attributes of each credential
            for cred in credentials:
                logger.debug(f"Credential object: {cred}, Username: {cred.username}, Password: {cred.password}")

            # Initialize EC2 service manager with our logger
            ec2_service = EC2ServiceManager(logger)
            
            # Convert credentials to the format expected by EC2ServiceManager
            credential_dicts = [
                {"username": cred.username, "password": cred.password}
                for cred in credentials
            ]
            logger.debug(f"Credential dicts: {credential_dicts}")

            # Create instances using the new EC2ServiceManager
            instance_results = ec2_service.create_ec2_instances(
                credentials=credential_dicts,
                users_per_instance=config.jupyter.DEFAULT_USERS_PER_INSTANCE
            )


            if not instance_results:
                raise Exception("Failed to create EC2 instances")
            
            # Create EC2Instance records and prepare instance info
            instance_info = []
            for ec2_instance, users, pawsey_credentials in instance_results:
                instance = EC2Instance.objects.create(
                    booking=booking,
                    instance_id=ec2_instance.id,
                    public_dns=ec2_instance.public_dns_name
                )
                instance_info.append((instance, users, pawsey_credentials))
            
            booking.ec2_instances_created = True
            booking.save()
            
            return instance_info
            
        except Exception as e:
            logger.error(f"Error creating EC2 instances: {str(e)}", exc_info=True)
            return None

@transaction.atomic
def register(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            try:
                # Extract form data
                email = form.cleaned_data['email']
                booking_time = form.cleaned_data['booking_time']
                number_of_users = form.cleaned_data['number_of_users']
                
                logger.info(f"Processing registration for email: {email}, users: {number_of_users}")
                
                # Create booking
                booking = Booking.objects.create(
                    email=email,
                    booking_time=booking_time,
                    number_of_users=number_of_users
                )
                
                # Create user credentials
                credentials = BookingService.create_user_credentials(booking, number_of_users)
                
                # Send initial confirmation email
                EmailService.send_initial_confirmation(email, booking_time, credentials)
                
                # Create EC2 instances if not already created
                if not booking.ec2_instances_created:
                    instance_info = BookingService.create_instances(booking, credentials)
                    
                    if instance_info:
                        # Send instance details email
                        EmailService.send_instance_details(email, instance_info)
                    else:
                        logger.error(f"Failed to create EC2 instances for booking {booking.id}")
                        form.add_error(None, "Failed to create EC2 instances. Please try again later.")
                        return render(request, 'aws_ec2/register.html', {'form': form})
                
                logger.info(f"Registration process completed for booking {booking.id}")
                
                return render(request, 'aws_ec2/registration_success.html', {
                    'email': email,
                    'booking_time': booking_time,
                    'credentials': credentials,
                })
                
            except Exception as e:
                logger.error(f"Error processing booking: {str(e)}", exc_info=True)
                form.add_error(None, f"There was an error processing your booking: {str(e)}")
    else:
        form = BookingForm()
    
    return render(request, 'aws_ec2/register.html', {'form': form})