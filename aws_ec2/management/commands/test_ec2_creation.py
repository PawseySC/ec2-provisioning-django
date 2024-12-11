# aws_ec2/management/commands/test_ec2_creation.py

from django.core.management.base import BaseCommand
from aws_ec2.ec2_utils import create_ec2_instances
from aws_ec2.models import UserCredential

class Command(BaseCommand):
    help = 'Test EC2 instance creation'

    def handle(self, *args, **options):
        self.stdout.write("Testing EC2 instance creation...")
        
        # Create some dummy credentials
        dummy_credentials = [
            UserCredential(username='testuser1', password='testpass1'),
            UserCredential(username='testuser2', password='testpass2'),
        ]
        
        instances = create_ec2_instances(dummy_credentials)
        
        if instances:
            self.stdout.write(self.style.SUCCESS(f"Successfully created {len(instances)} EC2 instances"))
            for instance, users in instances:
                self.stdout.write(f"Instance ID: {instance.id}, Public DNS: {instance.public_dns_name}")
        else:
            self.stdout.write(self.style.ERROR("Failed to create EC2 instances"))
