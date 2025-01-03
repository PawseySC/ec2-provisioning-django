# ec2_utils/main.py
import boto3
from typing import List, Optional, Dict, Tuple
import secrets
from .instance_manager import EC2InstanceManager
from .security import SecurityGroupManager
from .config import config 
from .user_data import UserDataGenerator

class EC2ServiceManager:
    def __init__(self, logger):
        self.logger = logger
        self.ec2 = boto3.resource('ec2', region_name=config.aws.REGION)
        self.security_group_manager = SecurityGroupManager(self.ec2, self.logger)
        self.instance_manager = EC2InstanceManager(
            self.ec2,
            self.security_group_manager,
            self.logger
        )
        self.user_data_generator = UserDataGenerator()

    def create_ec2_instances(self, 
                           credentials: List[Dict],
                           users_per_instance: int = 2) -> Optional[List[Tuple]]:
        """
        Orchestrates the creation of EC2 instances with JupyterHub.
        
        Args:
            credentials: List of user credentials
            users_per_instance: Number of users per instance
            
        Returns:
            Optional[List[Tuple]]: List of (instance, users, admin_credentials) or None
        """
        try:
            self.logger.info("Starting EC2 instance creation process")
            print(f"DEBUG: Received credentials in create_ec2_instances: {credentials}")
            
            # Set up security group
            security_group_id = self.security_group_manager.create_or_get_security_group(
                config.security_group.NAME,
                config.security_group.DESCRIPTION
            )
            print(f"DEBUG: Created/got security group ID: {security_group_id}")
            if not security_group_id:
                raise Exception("Failed to create/get security group")
            
            security_group = self.ec2.SecurityGroup(security_group_id)
            if not self.security_group_manager.setup_jupyter_security_rules(security_group):
                raise Exception("Failed to set up security rules")

            # Prepare instance configurations
            instance_configs = []
            for i in range(0, len(credentials), users_per_instance):
                instance_users = credentials[i:i + users_per_instance]
                print(f"DEBUG: Processing instance users: {instance_users}")
                self.logger.info(f"Creating instance {len(instance_configs) + 1} with {len(instance_users)} users:")
                for user in instance_users:
                    self.logger.info(f"- Username: {user['username']}")
            
                admin_password = secrets.token_hex(16)
                
                try:
                    user_data = self.user_data_generator.generate_full_script(
                        admin_password=admin_password,
                        users=instance_users,
                        requirements_url=config.jupyter.REQUIREMENTS_URL
                    )
                    print("DEBUG: Successfully generated user data script")
                except Exception as e:
                    print(f"DEBUG: Error generating user data script: {str(e)}")
                    print(f"DEBUG: admin_password: {admin_password}")
                    print(f"DEBUG: instance_users: {instance_users}")
                    print(f"DEBUG: requirements_url: {config.jupyter.REQUIREMENTS_URL}")
                    raise
                
                instance_configs.append({
                    'user_data': user_data,
                    'users': instance_users,
                    'admin_credentials': {
                        'username': 'pawsey',
                        'password': admin_password
                    }
                })

            # Create instances
            instances = self.instance_manager.create_instances(
                instance_configs,
                config.aws.AMI_ID,
                config.aws.INSTANCE_TYPE,
                config.aws.KEY_NAME,
                security_group_id
            )

            # Wait for instances to be ready
            if not self.instance_manager.wait_for_instances(instances):
                raise Exception("Failed waiting for instances")

            self.logger.info("EC2 instance creation completed successfully")
            return instances

        except Exception as e:
            self.logger.error(f"Error in create_ec2_instances: {e}", exc_info=True)
            return None