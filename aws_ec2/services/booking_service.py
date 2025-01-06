import secrets
from typing import List, Tuple, Optional
from ..models import Booking, UserCredential, EC2Instance
from ..ec2_utils.main import EC2ServiceManager
from ..ec2_utils.config import config
from .logging_service import LoggingService

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
