# aws_ec2/services/booking_service.py
import secrets
from typing import List, Tuple, Optional
from ..models import Booking, UserCredential, EC2Instance
from ..ec2_utils.main import EC2ServiceManager
from ..ec2_utils.config import config
from .logging_service import LoggingService
from django.utils import timezone

logger = LoggingService.get_logger("booking_service")

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
            for cred in credentials:
                logger.debug(f"Credential object: {cred}, Username: {cred.username}, Password: {cred.password}")

            ec2_service = EC2ServiceManager(logger)
            
            credential_dicts = [
                {"username": cred.username, "password": cred.password}
                for cred in credentials
            ]
            logger.debug(f"Credential dicts: {credential_dicts}")

            instance_results = ec2_service.create_ec2_instances(
                credentials=credential_dicts,
                users_per_instance=config.jupyter.DEFAULT_USERS_PER_INSTANCE
            )

            if not instance_results:
                raise Exception("Failed to create EC2 instances")
            
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

    @staticmethod
    def schedule_instance_creation(booking: Booking):
        """
        Schedules the instance creation task for the booking time
        """
        try:
            from ..tasks import create_scheduled_instances
            
            # Calculate delay in seconds from now until booking time
            now = timezone.localtime(timezone.now(), booking.booking_time.tzinfo)
            delay = (booking.booking_time - now).total_seconds()
            
            if delay > 0:
                create_scheduled_instances.apply_async(
                    args=[booking.id],
                    eta=booking.booking_time
                )
                logger.info(f"Scheduled instance creation for booking {booking.id} at {booking.booking_time}")
                logger.info(f"Booking time: {booking.booking_time}")
                logger.info(f"Current time: {now}")
                logger.info(f"Booking time timezone: {booking.booking_time.tzinfo}")
                logger.info(f"Delay: {delay}")
                return True
            else:
                logger.error(f"Invalid delay for booking {booking.id}: {delay} seconds")
                return False
                
        except Exception as e:
            logger.error(f"Error scheduling instance creation: {str(e)}", exc_info=True)
            return False