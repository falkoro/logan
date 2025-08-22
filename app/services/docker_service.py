"""
Docker Service for managing containers via SSH
"""
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from app.models.container import Container, ContainerStatus, ContainerStats
from app.services.ssh_service import SSHService, SSHConnectionError

logger = logging.getLogger(__name__)

class DockerServiceError(Exception):
    """Docker service related errors"""
    pass

class DockerService:
    """Service for managing Docker containers on remote host"""
    
    def __init__(self, ssh_service: SSHService):
        self.ssh = ssh_service
        self._containers_cache: Dict[str, Container] = {}
        self._last_update: Optional[datetime] = None
        
    def list_containers(self, include_stopped: bool = True, quick_mode: bool = False) -> List[Container]:
        """
        List all containers on remote host
        
        Args:
            include_stopped: Include stopped containers in the list
            quick_mode: If True, only get basic info without stats and logs
            
        Returns:
            List of Container objects
        """
        try:
            # Build Docker command
            cmd_args = "ps -a --format json" if include_stopped else "ps --format json"
            
            exit_code, stdout, stderr = self.ssh.execute_docker_command(cmd_args)
            
            if exit_code != 0:
                logger.error(f"Failed to list containers: {stderr}")
                raise DockerServiceError(f"Failed to list containers: {stderr}")
            
            containers = []
            if stdout.strip():
                # Docker ps --format json returns one JSON object per line
                for line in stdout.strip().split('\n'):
                    try:
                        container_data = json.loads(line)
                        if quick_mode:
                            # Create container from basic ps data only
                            container = self._create_basic_container(container_data)
                            if container:
                                containers.append(container)
                        else:
                            # Get detailed information for each container
                            detailed_container = self.get_container_details(container_data['Names'])
                            if detailed_container:
                                containers.append(detailed_container)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse container JSON: {e}")
                        continue
            
            # Update cache
            if not quick_mode:
                self._containers_cache = {c.name: c for c in containers}
                self._last_update = datetime.now()
            
            return containers
            
        except SSHConnectionError as e:
            logger.error(f"SSH connection error while listing containers: {e}")
            raise DockerServiceError(f"Connection error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error listing containers: {e}")
            raise DockerServiceError(f"Unexpected error: {e}")
    
    def _create_basic_container(self, ps_data: Dict[str, Any]) -> Optional[Container]:
        """
        Create a basic container object from docker ps data
        
        Args:
            ps_data: Dictionary from docker ps JSON output
            
        Returns:
            Basic Container object or None if invalid data
        """
        try:
            # Map status to our enum
            state = ps_data.get('State', '').lower()
            if 'running' in state:
                status = ContainerStatus.RUNNING
            elif 'exited' in state:
                status = ContainerStatus.EXITED
            elif 'paused' in state:
                status = ContainerStatus.PAUSED
            else:
                status = ContainerStatus.CREATED
            
            # Create basic container
            container = Container(
                id=ps_data.get('ID', ''),
                name=ps_data.get('Names', '').lstrip('/'),  # Remove leading slash
                image=ps_data.get('Image', ''),
                status=status,
                is_running=status == ContainerStatus.RUNNING,
                created=ps_data.get('CreatedAt', ''),
                ports=ps_data.get('Ports', '').split(', ') if ps_data.get('Ports') else [],
                command=ps_data.get('Command', ''),
                size=ps_data.get('Size', ''),
                networks=ps_data.get('Networks', '').split(', ') if ps_data.get('Networks') else []
            )
            
            return container
            
        except Exception as e:
            logger.error(f"Failed to create basic container from ps data: {e}")
            return None
    
    def get_container_details(self, container_name: str) -> Optional[Container]:
        """
        Get detailed information about a specific container
        
        Args:
            container_name: Name or ID of the container
            
        Returns:
            Container object or None if not found
        """
        try:
            exit_code, stdout, stderr = self.ssh.execute_docker_command(f"inspect {container_name}")
            
            if exit_code != 0:
                logger.error(f"Failed to inspect container {container_name}: {stderr}")
                return None
            
            container_data = json.loads(stdout)[0]  # inspect returns a list
            container = Container.from_docker_dict(container_data)
            
            # Get container stats if running
            if container.is_running:
                stats = self.get_container_stats(container_name)
                container.stats = stats
            
            # Get recent logs
            logs = self.ssh.get_container_logs(container_name, lines=10)
            container.logs_tail = logs
            
            return container
            
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            logger.error(f"Failed to parse container details for {container_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting container details for {container_name}: {e}")
            return None
    
    def get_container_stats(self, container_name: str) -> Optional[ContainerStats]:
        """
        Get resource statistics for a container
        
        Args:
            container_name: Name or ID of the container
            
        Returns:
            ContainerStats object or None if not available
        """
        try:
            # Get stats without streaming (--no-stream)
            exit_code, stdout, stderr = self.ssh.execute_docker_command(
                f"stats --no-stream --format json {container_name}",
                timeout=15
            )
            
            if exit_code != 0:
                logger.warning(f"Failed to get stats for {container_name}: {stderr}")
                return None
            
            if not stdout.strip():
                return None
                
            stats_data = json.loads(stdout.strip().split('\n')[0])  # First line
            
            # Parse memory usage
            memory_usage = stats_data.get('MemUsage', '0B / 0B')
            memory_parts = memory_usage.split(' / ')
            memory_used_str = memory_parts[0].strip()
            memory_limit_str = memory_parts[1].strip() if len(memory_parts) > 1 else '0B'
            
            # Convert memory strings to bytes
            memory_used = self._parse_memory_string(memory_used_str)
            memory_limit = self._parse_memory_string(memory_limit_str)
            
            # Parse CPU percentage
            cpu_percent_str = stats_data.get('CPUPerc', '0.00%').rstrip('%')
            cpu_percent = float(cpu_percent_str) if cpu_percent_str else 0.0
            
            # Parse memory percentage
            mem_percent_str = stats_data.get('MemPerc', '0.00%').rstrip('%')
            mem_percent = float(mem_percent_str) if mem_percent_str else 0.0
            
            # Parse network I/O
            net_io = stats_data.get('NetIO', '0B / 0B')
            net_parts = net_io.split(' / ')
            net_rx = self._parse_memory_string(net_parts[0].strip()) if len(net_parts) > 0 else 0
            net_tx = self._parse_memory_string(net_parts[1].strip()) if len(net_parts) > 1 else 0
            
            return ContainerStats(
                cpu_percent=cpu_percent,
                memory_usage=memory_used,
                memory_limit=memory_limit,
                memory_percent=mem_percent,
                network_rx=net_rx,
                network_tx=net_tx,
                timestamp=datetime.now()
            )
            
        except (json.JSONDecodeError, ValueError, IndexError) as e:
            logger.warning(f"Failed to parse stats for {container_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting stats for {container_name}: {e}")
            return None
    
    def _parse_memory_string(self, mem_str: str) -> int:
        """
        Parse memory string (e.g., '1.5GB', '512MB') to bytes
        
        Args:
            mem_str: Memory string to parse
            
        Returns:
            Memory in bytes
        """
        if not mem_str or mem_str == '0B':
            return 0
        
        mem_str = mem_str.strip().upper()
        units = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
        
        for unit, multiplier in units.items():
            if mem_str.endswith(unit):
                try:
                    value = float(mem_str[:-len(unit)])
                    return int(value * multiplier)
                except ValueError:
                    return 0
        
        # Try to parse as plain number (assume bytes)
        try:
            return int(float(mem_str))
        except ValueError:
            return 0
    
    def start_container(self, container_name: str) -> bool:
        """
        Start a container
        
        Args:
            container_name: Name or ID of the container
            
        Returns:
            True if successful, False otherwise
        """
        try:
            exit_code, stdout, stderr = self.ssh.execute_docker_command(f"start {container_name}")
            
            if exit_code == 0:
                logger.info(f"Container {container_name} started successfully")
                return True
            else:
                logger.error(f"Failed to start container {container_name}: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting container {container_name}: {e}")
            return False
    
    def stop_container(self, container_name: str, timeout: int = 10) -> bool:
        """
        Stop a container
        
        Args:
            container_name: Name or ID of the container
            timeout: Timeout in seconds before force kill
            
        Returns:
            True if successful, False otherwise
        """
        try:
            exit_code, stdout, stderr = self.ssh.execute_docker_command(
                f"stop --time {timeout} {container_name}"
            )
            
            if exit_code == 0:
                logger.info(f"Container {container_name} stopped successfully")
                return True
            else:
                logger.error(f"Failed to stop container {container_name}: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error stopping container {container_name}: {e}")
            return False
    
    def restart_container(self, container_name: str, timeout: int = 10) -> bool:
        """
        Restart a container
        
        Args:
            container_name: Name or ID of the container
            timeout: Timeout in seconds before force kill
            
        Returns:
            True if successful, False otherwise
        """
        try:
            exit_code, stdout, stderr = self.ssh.execute_docker_command(
                f"restart --time {timeout} {container_name}"
            )
            
            if exit_code == 0:
                logger.info(f"Container {container_name} restarted successfully")
                return True
            else:
                logger.error(f"Failed to restart container {container_name}: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error restarting container {container_name}: {e}")
            return False
    
    def get_container_logs(self, container_name: str, lines: int = 100, follow: bool = False) -> List[str]:
        """
        Get container logs
        
        Args:
            container_name: Name or ID of the container
            lines: Number of log lines to retrieve
            follow: Follow log output (not recommended for API calls)
            
        Returns:
            List of log lines
        """
        return self.ssh.get_container_logs(container_name, lines)
    
    def get_docker_system_info(self) -> Dict[str, Any]:
        """
        Get Docker system information
        
        Returns:
            Dictionary containing Docker system info
        """
        return self.ssh.get_docker_info()
    
    def prune_containers(self, filters: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Remove stopped containers
        
        Args:
            filters: Optional filters for pruning
            
        Returns:
            Dictionary with pruning results
        """
        try:
            cmd_args = "container prune -f"
            if filters:
                filter_args = " ".join([f"--filter {k}={v}" for k, v in filters.items()])
                cmd_args += f" {filter_args}"
            
            exit_code, stdout, stderr = self.ssh.execute_docker_command(cmd_args)
            
            result = {
                'success': exit_code == 0,
                'output': stdout,
                'error': stderr
            }
            
            if exit_code == 0:
                logger.info("Container pruning completed successfully")
            else:
                logger.error(f"Container pruning failed: {stderr}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during container pruning: {e}")
            return {
                'success': False,
                'error': str(e),
                'output': ''
            }
    
    def check_container_health(self, container_name: str) -> Optional[Dict[str, Any]]:
        """
        Check container health status
        
        Args:
            container_name: Name or ID of the container
            
        Returns:
            Dictionary with health check results or None
        """
        try:
            container = self.get_container_details(container_name)
            if not container:
                return None
            
            return {
                'name': container.name,
                'status': container.status.value,
                'health_status': container.health_status,
                'is_running': container.is_running,
                'is_healthy': container.is_healthy,
                'uptime': container.uptime
            }
            
        except Exception as e:
            logger.error(f"Error checking health for container {container_name}: {e}")
            return None
