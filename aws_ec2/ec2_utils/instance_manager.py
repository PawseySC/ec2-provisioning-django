# ec2_utils/instance_manager.py
from typing import List, Tuple, Optional, Dict
import time
from datetime import datetime, timedelta
import logging
import boto3
import json
import pytz

class EC2InstanceManager:
    def __init__(self, ec2_resource, security_group_manager, logger: logging.Logger):
        self.ec2 = ec2_resource
        self.security_group_manager = security_group_manager
        self.logger = logger
        self.timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.events_client = boto3.client('events')
        self.lambda_client = boto3.client('lambda')
        
        # Define the application timezone
        self.app_timezone = pytz.timezone('Australia/Perth')

    def schedule_instance_shutdown(self, instance_id: str, shutdown_delay_minutes: int = 10) -> bool:
        """
        Schedules an instance to shut down after specified minutes using EventBridge.
        Handles timezone conversion from local time (Australia/Perth) to UTC.
        
        Args:
            instance_id: EC2 instance ID
            shutdown_delay_minutes: Minutes until shutdown
            
        Returns:
            bool: True if scheduling successful
        """
        try:
            # Get current time in application timezone
            local_now = datetime.now(self.app_timezone)
            
            # Calculate shutdown time in local timezone
            local_shutdown_time = local_now + timedelta(minutes=shutdown_delay_minutes)
            
            # Convert to UTC for EventBridge
            utc_shutdown_time = local_shutdown_time.astimezone(pytz.UTC)
            
            # Create the cron expression using UTC time
            cron_expression = f"cron({utc_shutdown_time.minute} {utc_shutdown_time.hour} {utc_shutdown_time.day} {utc_shutdown_time.month} ? {utc_shutdown_time.year})"
            
            rule_name = f"shutdown-{instance_id}-{self.timestamp}"
            
            self.logger.info(f"Creating EventBridge rule for local time {local_shutdown_time} (UTC: {utc_shutdown_time})")
            self.logger.info(f"Using cron expression: {cron_expression}")
            
            # Create EventBridge rule
            response = self.events_client.put_rule(
                Name=rule_name,
                ScheduleExpression=cron_expression,
                State='ENABLED',
                Description=f'Auto shutdown rule for instance {instance_id}'
            )
            
            rule_arn = response['RuleArn']
            self.logger.info(f"EventBridge rule created: {rule_arn}")
            
            # Get Lambda function ARN
            lambda_function_name = 'stop-ec2-instance'
            lambda_arn = f'arn:aws:lambda:{self.ec2.meta.client.meta.region_name}:{self.get_account_id()}:function:{lambda_function_name}'
            
            # Add permission for EventBridge to invoke Lambda
            try:
                self.lambda_client.add_permission(
                    FunctionName=lambda_function_name,
                    StatementId=f'EventBridge-{rule_name}',
                    Action='lambda:InvokeFunction',
                    Principal='events.amazonaws.com',
                    SourceArn=rule_arn
                )
                self.logger.info(f"Added permission for EventBridge to invoke Lambda function")
            except self.lambda_client.exceptions.ResourceConflictException:
                # Permission might already exist, which is fine
                self.logger.info("Lambda permission already exists or conflicts - continuing")
            
            # Create target for stopping the instance
            target_response = self.events_client.put_targets(
                Rule=rule_name,
                Targets=[{
                    'Id': f'ShutdownTarget-{instance_id}',
                    'Arn': lambda_arn,
                    'Input': json.dumps({
                        "instance_id": instance_id
                    })
                }]
            )
            
            self.logger.info(f"EventBridge target created: {target_response}")
            self.logger.info(f"Scheduled shutdown for instance {instance_id} at {local_shutdown_time} local time")
            return True
            
        except Exception as e:
            self.logger.error(f"Error scheduling instance shutdown: {str(e)}", exc_info=True)
            return False

    def get_account_id(self) -> str:
        """Get the current AWS account ID"""
        sts = boto3.client('sts')
        return sts.get_caller_identity()['Account']

    def create_instances(self, 
                        instance_configs: List[Dict],
                        ami_id: str,
                        instance_type: str,
                        key_name: str,
                        security_group_id: str) -> List[Tuple]:
        """
        Creates EC2 instances based on provided configurations.
        
        Args:
            instance_configs: List of configurations for each instance
            ami_id: AMI ID to use
            instance_type: EC2 instance type
            key_name: SSH key pair name
            security_group_id: Security group ID
            
        Returns:
            List[Tuple]: List of (instance, users, admin_credentials) tuples
        """
        instances = []
        
        for i, config in enumerate(instance_configs, 1):
            try:
                self.logger.info(f"Creating EC2 instance {i}")
                
                instance = self.ec2.create_instances(
                    ImageId=ami_id,
                    MinCount=1,
                    MaxCount=1,
                    InstanceType=instance_type,
                    KeyName=key_name,
                    UserData=config['user_data'],
                    SecurityGroupIds=[security_group_id],
                    TagSpecifications=[{
                        'ResourceType': 'instance',
                        'Tags': [{
                            'Key': 'Name',
                            'Value': f'TLJH-Instance-{i}-{self.timestamp}'
                        }]
                    }]
                )[0]

                # Schedule instance shutdown
                if not self.schedule_instance_shutdown(instance.id):
                    self.logger.warning(f"Failed to schedule shutdown for instance {instance.id}")
                
                instances.append((
                    instance,
                    config['users'],
                    config['admin_credentials']
                ))
                
                self.logger.info(f"Created instance {i} with ID: {instance.id}")
                
            except Exception as e:
                self.logger.error(f"Error creating instance {i}: {e}")
                raise
                
        return instances

    def wait_for_instances(self, instances: List[Tuple], timeout: int = 300) -> bool:
        """
        Waits for instances to be in running state and ready for use.
        
        Args:
            instances: List of instance tuples
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if all instances are ready
        """
        try:
            self.logger.info("Waiting for instances to be ready...")
            start_time = time.time()
            
            for i, (instance, _, _) in enumerate(instances, 1):
                remaining_time = timeout - (time.time() - start_time)
                if remaining_time <= 0:
                    raise TimeoutError("Timeout waiting for instances")
                
                instance.wait_until_running(
                    WaiterConfig={'Delay': 5, 'MaxAttempts': int(remaining_time/5)}
                )
                instance.reload()
                
                self.logger.info(f"Instance {i} (ID: {instance.id}) is running")
                
            # Additional wait for TLJH installation
            self.logger.info("Waiting for TLJH installation...")
            time.sleep(180)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error waiting for instances: {e}")
            return False
