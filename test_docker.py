"""
Test script to debug container retrieval
"""
import os
import sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ssh_service import SSHService
from app.services.docker_service import DockerService
from app.config.settings import Config

def test_docker_connection():
    """Test Docker connection and container retrieval"""
    print("=== Testing LoganGemma Docker Connection ===")
    print(f"Test started at: {datetime.now()}")
    
    try:
        # Initialize config
        print("1. Loading configuration...")
        config = Config()
        print(f"Remote host: {config.REMOTE_HOST}")
        print(f"Remote user: {config.REMOTE_USER}")
        print(f"SSH key path: {config.SSH_KEY_PATH}")
        print()
        
        # Initialize SSH service
        print("2. Initializing SSH service...")
        ssh_service = SSHService(config)
        
        # Test SSH connection
        print("3. Testing SSH connection...")
        exit_code, stdout, stderr = ssh_service.execute_command("echo 'SSH connection successful'")
        if exit_code == 0:
            print(f"   ✅ SSH connection successful: {stdout.strip()}")
        else:
            print(f"   ❌ SSH connection failed: {stderr}")
            return
        
        # Test Docker command
        print("4. Testing Docker command...")
        exit_code, stdout, stderr = ssh_service.execute_command("docker --version")
        if exit_code == 0:
            print(f"   ✅ Docker available: {stdout.strip()}")
        else:
            print(f"   ❌ Docker not available: {stderr}")
            return
        
        # Initialize Docker service
        print("5. Initializing Docker service...")
        docker_service = DockerService(ssh_service)
        
        # List containers
        print("6. Listing containers...")
        containers = docker_service.list_containers()
        
        print(f"   ✅ Found {len(containers)} containers:")
        for i, container in enumerate(containers, 1):
            status_emoji = "🟢" if container.is_running else "🔴"
            print(f"   {i:2d}. {status_emoji} {container.name}")
            print(f"       Image: {container.image}")
            print(f"       Status: {container.status}")
            print(f"       Ports: {', '.join(container.ports) if container.ports else 'None'}")
            print()
        
        print("=== Test completed successfully! ===")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_docker_connection()
