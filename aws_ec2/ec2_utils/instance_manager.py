# ec2_utils/instance_manager.py
from typing import List, Tuple, Optional, Dict
import time
from datetime import datetime
import logging

class EC2InstanceManager:
    def __init__(self, ec2_resource, security_group_manager, logger: logging.Logger):
        self.ec2 = ec2_resource
        self.security_group_manager = security_group_manager
        self.logger = logger
        self.timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

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
