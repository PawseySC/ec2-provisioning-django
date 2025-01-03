# refactored into ec2_utils folder
import boto3
from botocore.exceptions import ClientError
import math
import logging
import time
import secrets
from datetime import datetime

# Create a unique timestamp string
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a file handler
handler = logging.FileHandler('ec2_creation.log')
handler.setLevel(logging.DEBUG)

# Create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)

def create_or_get_security_group(ec2, group_name, description):
    try:
        logger.info(f"Attempting to create or get security group: {group_name}")
        existing_groups = ec2.security_groups.all()
        for group in existing_groups:
            if group.group_name == group_name:
                logger.info(f"Security group '{group_name}' already exists. Using existing group.")
                return group.id

        security_group = ec2.create_security_group(
            GroupName=group_name,
            Description=description
        )
        logger.info(f"Created new security group: {group_name} with ID: {security_group.id}")
        return security_group.id

    except ClientError as e:
        logger.error(f"Error creating or retrieving security group: {e}")
        return None

def authorize_ingress_if_not_exists(security_group, ip_protocol, from_port, to_port, cidr_ip):
    try:
        logger.info(f"Attempting to authorize ingress for {ip_protocol} from {cidr_ip} on port {from_port}-{to_port}")
        security_group.authorize_ingress(
            IpProtocol=ip_protocol,
            FromPort=from_port,
            ToPort=to_port,
            CidrIp=cidr_ip
        )
        logger.info(f"Authorized ingress: {ip_protocol} from {cidr_ip} on port {from_port}-{to_port}")
    except ClientError as e:
        if 'InvalidPermission.Duplicate' in str(e):
            logger.info(f"Ingress rule already exists: {ip_protocol} from {cidr_ip} on port {from_port}-{to_port}")
        else:
            logger.error(f"Error authorizing ingress: {e}")

def create_ec2_instances(credentials, users_per_instance=2):
    try:
        logger.info("Starting EC2 instance creation process")
        
        requirements_url = "https://raw.githubusercontent.com/PawseySC/quantum-computing-hackathon/main/python/requirements.txt"
        
        ec2 = boto3.resource('ec2', region_name='ap-southeast-2')
        
        num_users = len(credentials)
        num_instances = math.ceil(num_users / users_per_instance)
        logger.info(f"Planning to create {num_instances} instances for {num_users} users")

        security_group_id = create_or_get_security_group(ec2, 'TLJH-SG', 'Security group for TLJH EC2 instances')

        if security_group_id is None:
            logger.error("Failed to create or get security group")
            return None

        security_group = ec2.SecurityGroup(security_group_id)

        authorize_ingress_if_not_exists(security_group, 'tcp', 22, 22, '0.0.0.0/0')
        authorize_ingress_if_not_exists(security_group, 'tcp', 80, 80, '0.0.0.0/0')
        authorize_ingress_if_not_exists(security_group, 'tcp', 443, 443, '0.0.0.0/0')

        # Generate a secure password for Pawsey admin user
        pawsey_password = secrets.token_hex(16)
        logger.info("Generated password for Pawsey admin user")

        instances = []
        for i in range(num_instances):
            instance_users = credentials[i*users_per_instance:(i+1)*users_per_instance]
            
            logger.info(f"Generating user data script for instance {i+1}")
            logger.info(f"Users for instance {i+1}: {[user.username for user in instance_users]}")

            # Create Pawsey admin user setup commands
            pawsey_setup = f"""
# Create Pawsey admin user
sudo useradd -m -s /bin/bash pawsey
echo 'pawsey:{pawsey_password}' | sudo chpasswd
sudo usermod -aG sudo pawsey

# Create sudoers file for Pawsey user
echo 'pawsey ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/pawsey
sudo chmod 0440 /etc/sudoers.d/pawsey
"""

            # Create user creation commands
            user_creation_commands = []
            for user in instance_users:
                user_creation_commands.extend([
                    f"sudo useradd -m -s /bin/bash {user.username}",
                    f"echo '{user.username}:{user.password}' | sudo chpasswd",
                    f"sudo usermod -aG jupyter {user.username}",
                    f"sudo tljh-config add-item auth.PAMAuthenticator.whitelist {user.username}",
                ])

            user_creation = "\n".join(user_creation_commands)
            
            user_data_script = f"""#!/bin/bash
set -e

# Update system
sudo apt-get update
sudo apt-get install -y python3-pip

# Create and configure the getlesson script
sudo echo "#!/bin/bash\n 
git clone https://github.com/PawseySC/quantum-computing-hackathon" >> /usr/bin/getlesson
sudo chmod a+rx /usr/bin/getlesson


# Set up Pawsey admin user
{pawsey_setup}

# Install TLJH with Pawsey as admin and include requirements
curl -L https://tljh.jupyter.org/bootstrap.py | sudo python3 - --admin pawsey --user-requirements-txt-url {requirements_url} --show-progress-page

# Wait for TLJH installation to complete
echo "Waiting for TLJH installation to complete..."
while [ ! -f /opt/tljh/installer.log ] || ! grep -q "Done!" /opt/tljh/installer.log; do
    sleep 30
    echo "Still waiting for TLJH installation..."
done

# Configure JupyterHub
sudo tljh-config set auth.type jupyterhub.auth.PAMAuthenticator
sudo tljh-config set auth.PAMAuthenticator.open_sessions False

# Create jupyter group if it doesn't exist
sudo groupadd -f jupyter

# Create regular users and set up permissions
{user_creation}

# Remove sudo access from regular users
for username in {' '.join([user.username for user in instance_users])}; do
    sudo deluser $username sudo 2>/dev/null || true
done

# Reload JupyterHub configuration
sudo tljh-config reload

# Verify installation
echo "Verifying Pawsey admin user..."
if id "pawsey" >/dev/null 2>&1; then
    echo "Pawsey admin user created successfully"
else
    echo "Failed to create Pawsey admin user"
    exit 1
fi

echo "Verifying JupyterHub users..."
for username in {' '.join([user.username for user in instance_users])}; do
    if id "$username" >/dev/null 2>&1; then
        echo "User $username created successfully"
    else
        echo "Failed to create user $username"
        exit 1
    fi
done

echo "Installation, PAM authentication setup, and user creation completed!"
"""

            logger.debug(f"User data script for instance {i+1}:\n{user_data_script}")
            
            logger.info(f"Attempting to create EC2 instance {i+1}")
            ec2_instance = ec2.create_instances(
                ImageId='ami-0892a9c01908fafd1',
                MinCount=1,
                MaxCount=1,
                InstanceType='t3.micro', #t2.large m5.large t2.micro t3.medium t3.micro 
                KeyName='aws_00',
                UserData=user_data_script,
                SecurityGroupIds=[security_group_id],
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [{'Key': 'Name', 'Value': f'TLJH-Instance-{i+1}-{timestamp}'}]
                    }
                ]
            )[0]
            
            logger.info(f"EC2 instance {i+1} created with ID: {ec2_instance.id}")
            instances.append((ec2_instance, instance_users, {'username': 'pawsey', 'password': pawsey_password}))

        logger.info("Waiting for all instances to be in 'running' state")
        for j, (instance, _, _) in enumerate(instances, 1):
            instance.wait_until_running()
            instance.reload()
            logger.info(f"Instance {j} (ID: {instance.id}) is now running")

        # Add additional wait time for TLJH installation and user setup
        logger.info("Waiting additional time for TLJH installation and user setup...")
        time.sleep(180)  # Wait 3 minutes for setup to complete

        logger.info("EC2 instance creation process completed successfully")
        return instances

    except Exception as e:
        logger.error(f"Error creating EC2 instances: {e}", exc_info=True)
        return None
