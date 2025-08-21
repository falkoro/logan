"""Docker service for managing remote Docker containers via SSH."""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

from ..models.container import ContainerModel
from .ssh_service import SSHService

logger = logging.getLogger(__name__)


class DockerService:
    """Service for managing Docker containers on remote hosts."""
    
    def __init__(self, ssh_service: SSHService, managed_services: Dict[str, Any]):
        """Initialize Docker service.
        
        Args:
            ssh_service: SSH service for remote connections
            managed_services: Dictionary of managed services configuration
        """
        self.ssh = ssh_service
        self.managed_services = managed_services
        
    def list_containers(self, all_containers: bool = True) -> List[ContainerModel]:
        """List all containers on the remote host.
        
        Args:
            all_containers: If True, list all containers, otherwise only running ones
            
        Returns:
            List of ContainerModel objects
        """
        try:
            cmd = "ps -a --format json" if all_containers else "ps --format json"
            exit_code, stdout, stderr = self.ssh.execute_docker_command(cmd)
            
            if exit_code != 0:
                logger.error(f"Failed to list containers: {stderr}")
                return []
            
            if not stdout.strip():
                logger.info("No containers found")
                return []
            
            # Parse JSON output
            containers = []
            try:
                # Docker ps --format json outputs one JSON object per line
                for line in stdout.strip().split('\n'):
                    if line.strip():
                        container_data = json.loads(line)
                        containers.append(self._parse_container_summary(container_data))
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse container list JSON: {e}")
                return []
            
            return containers
            
        except Exception as e:
            logger.error(f"Error listing containers: {e}")
            return []
    
    def get_container_details(self, container_id_or_name: str) -> Optional[ContainerModel]:
        """Get detailed information about a specific container.
        
        Args:
            container_id_or_name: Container ID or name
            
        Returns:
            ContainerModel object or None if not found
        """
        try:
            cmd = f"inspect {container_id_or_name}"
            exit_code, stdout, stderr = self.ssh.execute_docker_command(cmd)
            
            if exit_code != 0:
                logger.error(f"Failed to inspect container {container_id_or_name}: {stderr}")
                return None
            
            try:
                container_data = json.loads(stdout)
                if isinstance(container_data, list) and container_data:
                    container_info = container_data[0]
                    return self._parse_container_details(container_info)
                else:
                    logger.error("Invalid container inspect response")
                    return None
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse container details JSON: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting container details: {e}")
            return None
    
    def start_container(self, container_id_or_name: str) -> bool:
        """Start a container.
        
        Args:
            container_id_or_name: Container ID or name
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cmd = f"start {container_id_or_name}"
            exit_code, stdout, stderr = self.ssh.execute_docker_command(cmd)
            
            if exit_code == 0:
                logger.info(f"Container {container_id_or_name} started successfully")
                return True
            else:
                logger.error(f"Failed to start container {container_id_or_name}: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting container: {e}")
            return False
    
    def stop_container(self, container_id_or_name: str, timeout: int = 10) -> bool:
        """Stop a container.
        
        Args:
            container_id_or_name: Container ID or name
            timeout: Graceful shutdown timeout in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cmd = f"stop --time {timeout} {container_id_or_name}"
            exit_code, stdout, stderr = self.ssh.execute_docker_command(cmd, timeout=timeout + 10)
            
            if exit_code == 0:
                logger.info(f"Container {container_id_or_name} stopped successfully")
                return True
            else:
                logger.error(f"Failed to stop container {container_id_or_name}: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error stopping container: {e}")
            return False
    
    def restart_container(self, container_id_or_name: str, timeout: int = 10) -> bool:
        """Restart a container.
        
        Args:
            container_id_or_name: Container ID or name  
            timeout: Graceful shutdown timeout in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cmd = f"restart --time {timeout} {container_id_or_name}"
            exit_code, stdout, stderr = self.ssh.execute_docker_command(cmd, timeout=timeout + 20)
            
            if exit_code == 0:
                logger.info(f"Container {container_id_or_name} restarted successfully")
                return True
            else:
                logger.error(f"Failed to restart container {container_id_or_name}: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error restarting container: {e}")
            return False
    
    def get_container_logs(self, container_id_or_name: str, tail: int = 100, 
                          since: Optional[str] = None) -> str:
        """Get container logs.
        
        Args:
            container_id_or_name: Container ID or name
            tail: Number of lines to show from end of logs
            since: Show logs since timestamp (e.g., "2023-01-01T00:00:00")
            
        Returns:
            str: Container logs
        """
        try:
            cmd = f"logs --tail {tail}"
            if since:
                cmd += f" --since {since}"
            cmd += f" {container_id_or_name}"
            
            exit_code, stdout, stderr = self.ssh.execute_docker_command(cmd, timeout=60)
            
            if exit_code == 0:
                return stdout
            else:
                logger.error(f"Failed to get logs for container {container_id_or_name}: {stderr}")
                return f"Error getting logs: {stderr}"
                
        except Exception as e:
            logger.error(f"Error getting container logs: {e}")
            return f"Error: {str(e)}"
    
    def get_container_stats(self, container_id_or_name: str) -> Dict[str, Any]:
        """Get real-time container resource usage statistics.
        
        Args:
            container_id_or_name: Container ID or name
            
        Returns:
            Dict containing resource usage statistics
        """
        try:
            cmd = f"stats --no-stream --format json {container_id_or_name}"
            exit_code, stdout, stderr = self.ssh.execute_docker_command(cmd, timeout=30)
            
            if exit_code == 0 and stdout.strip():
                try:
                    stats_data = json.loads(stdout.strip())
                    return stats_data
                except json.JSONDecodeError:
                    logger.error("Failed to parse container stats JSON")
                    return {}
            else:
                logger.error(f"Failed to get stats for container {container_id_or_name}: {stderr}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting container stats: {e}")
            return {}
    
    def get_managed_services_status(self) -> List[ContainerModel]:
        """Get status of all managed services.
        
        Returns:
            List of ContainerModel objects for managed services
        """
        all_containers = self.list_containers()
        managed_containers = []
        
        for container in all_containers:
            # Try to match container to managed service
            service_config = self._match_container_to_service(container)
            if service_config:
                # Update container with service information
                container.service_name = service_config.get('name')
                container.service_port = service_config.get('port')
                container.service_category = service_config.get('category')
                container.vpn_required = service_config.get('vpn_required', False)
                managed_containers.append(container)
        
        return managed_containers
    
    def _parse_container_summary(self, container_data: Dict[str, Any]) -> ContainerModel:
        """Parse container summary from Docker ps output.
        
        Args:
            container_data: Container data from Docker ps --format json
            
        Returns:
            ContainerModel object
        """
        # Docker ps JSON format has different field names than inspect
        container_id = container_data.get('ID', '')
        name = container_data.get('Names', '').lstrip('/')
        image = container_data.get('Image', '')
        status = container_data.get('Status', '')
        state = container_data.get('State', status)
        
        # Parse creation time from status
        created = datetime.now()
        created_str = container_data.get('CreatedAt', '')
        if created_str:
            try:
                # Try to parse various date formats
                created = datetime.strptime(created_str, '%Y-%m-%d %H:%M:%S %z')
            except ValueError:
                pass
        
        # Parse ports
        ports = {}
        ports_str = container_data.get('Ports', '')
        if ports_str:
            ports = self._parse_ports_string(ports_str)
        
        return ContainerModel(
            id=container_id,
            name=name,
            image=image,
            status=status,
            state=state,
            created=created,
            ports=ports
        )
    
    def _parse_container_details(self, container_data: Dict[str, Any]) -> ContainerModel:
        """Parse detailed container information from Docker inspect output.
        
        Args:
            container_data: Container data from Docker inspect
            
        Returns:
            ContainerModel object with service configuration if matched
        """
        service_config = self._match_container_data_to_service(container_data)
        return ContainerModel.from_docker_container(container_data, service_config)
    
    def _match_container_to_service(self, container: ContainerModel) -> Optional[Dict[str, Any]]:
        """Match a container to a managed service configuration.
        
        Args:
            container: ContainerModel object
            
        Returns:
            Service configuration dict or None
        """
        # Try exact name match first
        for service_key, service_config in self.managed_services.items():
            if service_config.get('container_name') == container.name:
                return service_config
        
        # Try partial name match
        for service_key, service_config in self.managed_services.items():
            service_name = service_config.get('container_name', '')
            if service_name and service_name in container.name:
                return service_config
        
        # Try image name match
        for service_key, service_config in self.managed_services.items():
            if service_key.lower() in container.image.lower():
                return service_config
        
        return None
    
    def _match_container_data_to_service(self, container_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Match container data to managed service configuration.
        
        Args:
            container_data: Container data from Docker API
            
        Returns:
            Service configuration dict or None
        """
        name = container_data.get('Name', '').lstrip('/')
        image = container_data.get('Config', {}).get('Image', '')
        
        # Try exact name match first
        for service_key, service_config in self.managed_services.items():
            if service_config.get('container_name') == name:
                return service_config
        
        # Try partial name match
        for service_key, service_config in self.managed_services.items():
            service_name = service_config.get('container_name', '')
            if service_name and service_name in name:
                return service_config
        
        # Try image name match
        for service_key, service_config in self.managed_services.items():
            if service_key.lower() in image.lower():
                return service_config
        
        return None
    
    def _parse_ports_string(self, ports_str: str) -> Dict[str, List[Dict[str, str]]]:
        """Parse ports string from Docker ps output.
        
        Args:
            ports_str: Ports string from Docker ps
            
        Returns:
            Ports dictionary in Docker inspect format
        """
        ports = {}
        if not ports_str:
            return ports
        
        # Parse port mappings like "0.0.0.0:8080->80/tcp"
        port_pattern = r'(?:(\d+\.\d+\.\d+\.\d+):)?(\d+)->(\d+)/(\w+)'
        matches = re.findall(port_pattern, ports_str)
        
        for match in matches:
            host_ip, host_port, container_port, protocol = match
            container_key = f"{container_port}/{protocol}"
            
            if container_key not in ports:
                ports[container_key] = []
            
            ports[container_key].append({
                'HostIp': host_ip or '0.0.0.0',
                'HostPort': host_port
            })
        
        return ports
