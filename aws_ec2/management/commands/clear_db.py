# aws_ec2/management/commands/clear_db.py
from django.core.management.base import BaseCommand
from aws_ec2.models import Booking, UserCredential, EC2Instance

class Command(BaseCommand):
    help = 'Clears all data from Booking, UserCredential, and EC2Instance models'

    def handle(self, *args, **kwargs):
        Booking.objects.all().delete()
        UserCredential.objects.all().delete()
        EC2Instance.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully cleared database'))

