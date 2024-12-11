# aws_ec2/urls.py
from django.urls import path
from . import views

app_name = 'aws_ec2'  # Namespace for the booking app

urlpatterns = [
    path('register/', views.register, name='register'),  # Path for the registration form
]

