from django.shortcuts import render
from django.db import transaction
from .models import Booking
from .forms import BookingForm
from .services.email_service import EmailService
from .services.booking_service import BookingService
from .services.logging_service import LoggingService

logger = LoggingService.get_logger("booking_views")

@transaction.atomic
def register(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            try:
                email = form.cleaned_data['email']
                booking_time = form.cleaned_data['booking_time']
                number_of_users = form.cleaned_data['number_of_users']
                
                logger.info(f"Processing registration for email: {email}, users: {number_of_users}")
                
                booking = Booking.objects.create(
                    email=email,
                    booking_time=booking_time,
                    number_of_users=number_of_users
                )
                
                credentials = BookingService.create_user_credentials(booking, number_of_users)
                EmailService.send_initial_confirmation(email, booking_time, credentials)
                
                if not booking.ec2_instances_created:
                    instance_info = BookingService.create_instances(booking, credentials)
                    
                    if instance_info:
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