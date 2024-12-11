# aws_ec2/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Booking, EC2Instance
from .ec2_utils import create_ec2_instances

import logging

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a file handler
handler = logging.FileHandler('signals.log')
handler.setLevel(logging.DEBUG)

# Create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)


@receiver(post_save, sender=Booking)
def create_ec2_instances_for_booking(sender, instance, created, **kwargs):
    if created and not instance.ec2_instances_created:
        logger.info(f"Signal received for new booking: {instance.id}")
        credentials = instance.user_credentials.all()
        logger.info(f"Creating EC2 instances for {len(credentials)} users")
        ec2_instances = create_ec2_instances(credentials)
        if ec2_instances:
            logger.info(f"Created {len(ec2_instances)} EC2 instances")
            for ec2_instance, users in ec2_instances:
                EC2Instance.objects.create(
                    booking=instance,
                    instance_id=ec2_instance.id,
                    public_dns=ec2_instance.public_dns_name
                )
                logger.info(f"Saved EC2 instance {ec2_instance.id} to database")
            instance.ec2_instances_created = True
            instance.save()
        else:
            logger.error("Failed to create EC2 instances")
