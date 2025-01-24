from django.apps import AppConfig


class AwsEc2Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'aws_ec2'

    def ready(self):
        import aws_ec2.tasks  # This imports the tasks
