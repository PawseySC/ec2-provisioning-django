# ec2_utils/security.py
from botocore.exceptions import ClientError
from typing import Optional, Tuple
import logging

class SecurityGroupManager:
    def __init__(self, ec2_resource, logger: logging.Logger):
        self.ec2 = ec2_resource
        self.logger = logger

    def create_or_get_security_group(self, group_name: str, description: str) -> Optional[str]:
        """
        Creates a new security group or retrieves an existing one.
        
        Args:
            group_name: Name of the security group
            description: Description of the security group
            
        Returns:
            str: Security group ID if successful, None otherwise
        """
        try:
            self.logger.info(f"Attempting to create or get security group: {group_name}")
            
            # Check for existing security group
            existing_groups = self.ec2.security_groups.all()
            for group in existing_groups:
                if group.group_name == group_name:
                    self.logger.info(f"Found existing security group: {group_name}")
                    return group.id

            # Create new security group if not found
            security_group = self.ec2.create_security_group(
                GroupName=group_name,
                Description=description
            )
            self.logger.info(f"Created new security group: {group_name} with ID: {security_group.id}")
            return security_group.id

        except ClientError as e:
            self.logger.error(f"Error creating/getting security group: {e}")
            return None

    def authorize_ingress_rule(self, security_group, ip_protocol: str, 
                             from_port: int, to_port: int, cidr_ip: str) -> bool:
        """
        Authorizes an ingress rule for the security group.
        
        Args:
            security_group: The security group object
            ip_protocol: The IP protocol (tcp, udp, etc.)
            from_port: Starting port
            to_port: Ending port
            cidr_ip: CIDR IP range
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info(
                f"Authorizing ingress: {ip_protocol} from {cidr_ip} "
                f"on ports {from_port}-{to_port}"
            )
            
            security_group.authorize_ingress(
                IpProtocol=ip_protocol,
                FromPort=from_port,
                ToPort=to_port,
                CidrIp=cidr_ip
            )
            return True

        except ClientError as e:
            if 'InvalidPermission.Duplicate' in str(e):
                self.logger.info(f"Ingress rule already exists")
                return True
            self.logger.error(f"Error authorizing ingress: {e}")
            return False

    def setup_jupyter_security_rules(self, security_group) -> bool:
        """
        Sets up all required security rules for JupyterHub.
        
        Args:
            security_group: The security group object
            
        Returns:
            bool: True if all rules were set up successfully
        """
        rules = [
            ('tcp', 22, 22, '0.0.0.0/0'),    # SSH
            ('tcp', 80, 80, '0.0.0.0/0'),    # HTTP
            ('tcp', 443, 443, '0.0.0.0/0'),  # HTTPS
        ]
        
        return all(
            self.authorize_ingress_rule(security_group, *rule)
            for rule in rules
        )