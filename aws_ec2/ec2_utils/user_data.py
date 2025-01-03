# ec2_utils/user_data.py
from typing import List, Dict
from string import Template

class UserDataGenerator:
    def __init__(self):
        self._base_script_template = self._get_base_script_template()
        
    def _get_base_script_template(self) -> Template:
        """Returns the base script template for user data."""
        return Template('''#!/bin/bash
set -e

# Update system
sudo apt-get update
sudo apt-get install -y python3-pip

# Create and configure the getlesson script
sudo echo "#!/bin/bash\n 
git clone https://github.com/PawseySC/quantum-computing-hackathon" >> /usr/bin/getlesson
sudo chmod a+rx /usr/bin/getlesson

# Set up Pawsey admin user
$pawsey_setup

# Install TLJH
curl -L https://tljh.jupyter.org/bootstrap.py | sudo python3 - --admin pawsey --user-requirements-txt-url $requirements_url --show-progress-page

# Wait for TLJH installation
echo "Waiting for TLJH installation to complete..."
while [ ! -f /opt/tljh/installer.log ] || ! grep -q "Done!" /opt/tljh/installer.log; do
    sleep 30
    echo "Still waiting for TLJH installation..."
done

# Configure JupyterHub
sudo tljh-config set auth.type jupyterhub.auth.PAMAuthenticator
sudo tljh-config set auth.PAMAuthenticator.open_sessions False

# Create jupyter group
sudo groupadd -f jupyter

# Create and configure users
$user_setup

# Remove sudo access from regular users
for username in $usernames; do
    sudo deluser $$username sudo 2>/dev/null || true
done

# Reload JupyterHub configuration
sudo tljh-config reload

# Verify installation
echo "Verifying installation..."
$verification_commands

echo "Installation completed successfully!"
''')

    def generate_pawsey_admin_setup(self, password: str) -> str:
        """
        Generates the Pawsey admin user setup commands.
        
        Args:
            password: Admin user password
            
        Returns:
            str: Setup commands for Pawsey admin user
        """
        return f'''
# Create Pawsey admin user
sudo useradd -m -s /bin/bash pawsey
echo 'pawsey:{password}' | sudo chpasswd
sudo usermod -aG sudo pawsey

# Create sudoers file for Pawsey user
echo 'pawsey ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/pawsey
sudo chmod 0440 /etc/sudoers.d/pawsey
'''

    def generate_user_setup(self, users: List[Dict]) -> str:
        """
        Generates user setup commands for regular users.
        
        Args:
            users: List of user credentials
            
        Returns:
            str: Setup commands for regular users
        """
        commands = []
        for user in users:
            commands.extend([
                f"sudo useradd -m -s /bin/bash {user['username']}",
                f"echo '{user['username']}:{user['password']}' | sudo chpasswd",
                f"sudo usermod -aG jupyter {user['username']}",
                f"sudo tljh-config add-item auth.PAMAuthenticator.whitelist {user['username']}"
            ])
        return '\n'.join(commands)

    def generate_verification_commands(self, users: List[Dict]) -> str:
        """
        Generates verification commands for user setup.
        
        Args:
            users: List of user credentials
            
        Returns:
            str: Commands to verify user setup
        """
        commands = ['echo "Verifying Pawsey admin user..."']
        commands.append('if id "pawsey" >/dev/null 2>&1; then')
        commands.append('    echo "Pawsey admin user created successfully"')
        commands.append('else')
        commands.append('    echo "Failed to create Pawsey admin user"')
        commands.append('    exit 1')
        commands.append('fi')
        
        commands.append('\necho "Verifying JupyterHub users..."')
        for user in users:
            commands.extend([
                f'if id "{user["username"]}" >/dev/null 2>&1; then',
                f'    echo "User {user["username"]} created successfully"',
                'else',
                f'    echo "Failed to create user {user["username"]}"',
                '    exit 1',
                'fi'
            ])
        
        return '\n'.join(commands)

    def generate_full_script(
        self,
        admin_password: str,
        users: List[Dict],
        requirements_url: str
    ) -> str:
        """
        Generates the complete user data script.
        
        Args:
            admin_password: Password for Pawsey admin user
            users: List of user credentials
            requirements_url: URL for requirements.txt
            
        Returns:
            str: Complete user data script
        """
        print(f"DEBUG: generate_full_script received:")
        print(f"- admin_password: {admin_password}")
        print(f"- users: {users}")
        print(f"- requirements_url: {requirements_url}")
        
        try:
            script = self._base_script_template.substitute(
                pawsey_setup=self.generate_pawsey_admin_setup(admin_password),
                requirements_url=requirements_url,
                user_setup=self.generate_user_setup(users),
                usernames=' '.join(user['username'] for user in users),
                verification_commands=self.generate_verification_commands(users)
            )
            print("DEBUG: Successfully generated script")
            return script
        except Exception as e:
            print(f"DEBUG: Error in generate_full_script: {str(e)}")
            print(f"DEBUG: Template variables:")
            print(f"- pawsey_setup: {self.generate_pawsey_admin_setup(admin_password)}")
            print(f"- user_setup: {self.generate_user_setup(users)}")
            print(f"- usernames: {' '.join(user['username'] for user in users)}")
            print(f"- verification_commands: {self.generate_verification_commands(users)}")
            raise