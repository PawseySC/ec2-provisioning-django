# tasks.py
from celery import shared_task
from django.utils import timezone
from .models import Booking
from .services.booking_service import BookingService
from .services.email_service import EmailService
from .services.logging_service import LoggingService

logger = LoggingService.get_logger("booking_tasks")

@shared_task
def create_scheduled_instances(booking_id: int):
    """
    Celery task to create EC2 instances for a scheduled booking
    """
    try:
        booking = Booking.objects.get(id=booking_id)
        
        if booking.ec2_instances_created:
            logger.warning(f"Instances already created for booking {booking_id}")
            return
            
        credentials = booking.user_credentials.all()
        
        if not credentials:
            logger.error(f"No credentials found for booking {booking_id}")
            return
            
        instance_info = BookingService.create_instances(booking, list(credentials))
        
        if instance_info:
            EmailService.send_instance_details(booking.email, instance_info)
            logger.info(f"Successfully created instances for booking {booking_id}")
        else:
            logger.error(f"Failed to create instances for booking {booking_id}")
            EmailService.send_creation_failure(booking.email)
            
    except Exception as e:
        logger.error(f"Error processing scheduled booking {booking_id}: {str(e)}", exc_info=True)
