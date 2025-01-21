#aws_ec2/services/email_service.py
from django.core.mail import send_mail
from django.conf import settings
from typing import List, Tuple
from ..models import UserCredential, EC2Instance

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
        instance_info: List[Tuple[EC2Instance, List[dict], dict]]
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
