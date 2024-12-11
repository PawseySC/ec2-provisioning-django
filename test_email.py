from django.core.mail import send_mail
from django.conf import settings

# Test email details
subject = "Test Email from Django"
message = "This is a test email to verify email settings."
from_email = settings.DEFAULT_FROM_EMAIL
recipient_list = ["victor.olet@outlook.com"]  # Replace with your email

# Send email
send_mail(subject, message, from_email, recipient_list)

