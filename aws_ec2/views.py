# booking/views.py
import secrets
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from .forms import BookingForm
from .models import Booking, UserCredential, EC2Instance
from django.conf import settings
from .ec2_utils import create_ec2_instances

import logging

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a file handler
handler = logging.FileHandler('views.log')
handler.setLevel(logging.DEBUG)

# Create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)


@transaction.atomic
def register(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            booking_time = form.cleaned_data['booking_time']
            number_of_users = form.cleaned_data['number_of_users']
            logger.info(f"Processing registration for email: {email}, users: {number_of_users}")
            
            try:
                booking = Booking.objects.create(email=email, booking_time=booking_time, number_of_users=number_of_users)
                logger.info(f"Created booking with ID: {booking.id}")
                
                credentials = []
                for _ in range(number_of_users):
                    username = secrets.token_hex(4)
                    password = secrets.token_hex(8)
                    credentials.append(UserCredential(booking=booking, username=username, password=password))
                UserCredential.objects.bulk_create(credentials)
                logger.info(f"Created {len(credentials)} user credentials for booking {booking.id}")
                
                # Send initial confirmation email
                credentials_list = []
                for cred in credentials:
                    credentials_list.append(f"Username: {cred.username}, Password: {cred.password}")
                
                credentials_str = "\n".join(credentials_list)
                
                subject = "Booking Confirmation"
                message = (
                    f"Dear User,\n\n"
                    f"Your booking has been successfully registered with the following details:\n\n"
                    f"Email: {email}\n"
                    f"Booking Time: {booking_time}\n\n"
                    f"Generated User Credentials:\n{credentials_str}\n\n"
                    f"JupyterHub URLs will be sent in a follow-up email once the instances are ready.\n\n"
                    f"Please keep this information secure for your records.\n\n"
                    f"Thank you for booking with us!"
                )
                from_email = settings.EMAIL_HOST_USER
                recipient_list = [email]
                send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                
                if not booking.ec2_instances_created:
                    logger.info(f"Initiating EC2 instance creation for booking {booking.id}")
                    ec2_instances = create_ec2_instances(credentials)
                    if ec2_instances:
                        instance_info = []
                        for ec2_instance, users, pawsey_credentials in ec2_instances:
                            instance = EC2Instance.objects.create(
                                booking=booking,
                                instance_id=ec2_instance.id,
                                public_dns=ec2_instance.public_dns_name
                            )
                            instance_info.append((instance, users, pawsey_credentials))
                        
                        booking.ec2_instances_created = True
                        booking.save()
                        
                        # Send follow-up email with JupyterHub URLs and Pawsey credentials
                        instance_details = []
                        for instance, users, pawsey_credentials in instance_info:
                            user_details = "\n".join([f"- {user.username}" for user in users])
                            instance_details.append(
                                f"Instance URL: http://{instance.public_dns}\n"
                                f"JupyterHub Users assigned to this instance:\n{user_details}\n"
                                f"\nAdmin Access Credentials (for system administration only):\n"
                                f"Username: {pawsey_credentials['username']}\n"
                                f"Password: {pawsey_credentials['password']}\n"
                            )
                        
                        instance_details_str = "\n".join(instance_details)
                        
                        subject = "JupyterHub Access Information"
                        message = (
                            f"Dear User,\n\n"
                            f"Your JupyterHub instances are now ready! Here are the access details:\n\n"
                            f"{instance_details_str}\n"
                            f"Important Notes:\n"
                            f"1. It may take up to 5-10 minutes for the JupyterHub services to fully initialize.\n"
                            f"2. Use the JupyterHub user credentials provided in the previous email to log in.\n"
                            f"3. The Pawsey admin credentials are for system administration only and should be kept secure.\n"
                            f"4. You may see a security warning about the certificate - this is expected for the demo environment.\n\n"
                            f"If you experience any issues accessing the service, please wait a few minutes and try again.\n\n"
                            f"Best regards,\n"
                            f"Your JupyterHub Team"
                        )
                        
                        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                        logger.info(f"Sent follow-up email with JupyterHub URLs and Pawsey credentials for booking {booking.id}")
                    else:
                        logger.error(f"Failed to create EC2 instances for booking {booking.id}")

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

