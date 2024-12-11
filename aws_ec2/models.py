# aws_ec2/models.py
import datetime
from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password



class Booking(models.Model):
    email = models.EmailField(unique=True)
    booking_time = models.DateTimeField(default=timezone.now)
    number_of_users = models.IntegerField(default=1)
    ec2_instances_created = models.BooleanField(default=False)

    def __str__(self):
        return f"Booking for {self.email} at {self.booking_time}"

class UserCredential(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='user_credentials')
    username = models.CharField(max_length=32, unique=True)
    password = models.CharField(max_length=64)

    def save(self, *args, **kwargs):
        if not self.pk:  # Only hash the password if it's a new instance
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Username: {self.username} for Booking ID: {self.booking.id}"

class EC2Instance(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='ec2_instances')
    instance_id = models.CharField(max_length=20)
    public_dns = models.CharField(max_length=255)

    def __str__(self):
        return f"EC2 Instance {self.instance_id} for Booking ID: {self.booking.id}"
