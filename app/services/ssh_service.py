"""
SSH Service for remote Docker host management
"""
import logging
import paramiko
import socket
from typing import Optional, Tuple, List, Dict, Any
from contextlib import contextmanager
from app.config.settings import Config

logger = logging.getLogger(__name__)

class SSHConnectionError(Exception):
    """SSH connection related errors"""
    pass

class SSHService:
    """Service for managing SSH connections to remote Docker host"""
    
    def __init__(self, config: Config):
        self.config = config
        self.host = config.REMOTE_HOST
        self.username = config.REMOTE_USER
        self.key_path = config.SSH_KEY_PATH
        self.timeout = config.SSH_TIMEOUT
        self._client: Optional[paramiko.SSHClient] = None
        
    def _get_ssh_client(self) -> paramiko.SSHClient:
        """Get or create SSH client connection"""
        if self._client is None or not self._is_connection_alive():
            self._connect()
        return self._client
    
    def _is_connection_alive(self) -> bool:
        """Check if SSH connection is still alive"""
        if self._client is None:
            return False
        try:
            transport = self._client.get_transport()
            return transport is not None and transport.is_alive()
        except Exception:
            return False
    
    def _connect(self) -> None:
        """Establish SSH connection"""
        try:
            if self._client:
                self._client.close()
            
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Try key-based authentication first
            try:
                self._client.connect(
                    hostname=self.host,
                    username=self.username,
                    key_filename=self.key_path,
                    timeout=self.timeout,
                    look_for_keys=True,
                    allow_agent=True
                )
                logger.info(f"SSH connection established to {self.host} using key authentication")
            except (paramiko.AuthenticationException, FileNotFoundError):
                # Fallback to password authentication if available
                logger.warning("Key authentication failed, you may need to set up SSH keys")
                raise SSHConnectionError(f"Failed to authenticate to {self.host}")
                
        except socket.timeout:
            raise SSHConnectionError(f"Connection timeout to {self.host}")
        except socket.gaierror:
            raise SSHConnectionError(f"Could not resolve hostname {self.host}")
        except Exception as e:
            logger.error(f"SSH connection failed: {str(e)}")
            raise SSHConnectionError(f"SSH connection failed: {str(e)}")
    
    def execute_command(self, command: str, timeout: Optional[int] = None) -> Tuple[int, str, str]:
        """
        Execute command on remote host
        
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        try:
            client = self._get_ssh_client()
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout or self.timeout)
            
            exit_code = stdout.channel.recv_exit_status()
            stdout_data = stdout.read().decode('utf-8')
            stderr_data = stderr.read().decode('utf-8')
            
            logger.debug(f"Command executed: {command[:100]}... | Exit code: {exit_code}")
            return exit_code, stdout_data, stderr_data
            
        except socket.timeout:
            raise SSHConnectionError("Command execution timeout")
        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            raise SSHConnectionError(f"Command execution failed: {str(e)}")
    
    def execute_docker_command(self, docker_args: str, timeout: Optional[int] = None) -> Tuple[int, str, str]:
        """
        Execute Docker command on remote host
        
        Args:
            docker_args: Docker command arguments (without 'docker')
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        command = f"docker {docker_args}"
        return self.execute_command(command, timeout)
    
    def test_connection(self) -> bool:
        """
        Test SSH connection to remote host
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            exit_code, stdout, stderr = self.execute_command("echo 'SSH connection test'", timeout=5)
            return exit_code == 0
        except SSHConnectionError:
            return False
    
    def test_docker_access(self) -> bool:
        """
        Test Docker access on remote host
        
        Returns:
            True if Docker is accessible, False otherwise
        """
        try:
            exit_code, stdout, stderr = self.execute_docker_command("version --format '{{.Server.Version}}'", timeout=10)
            if exit_code == 0 and stdout.strip():
                logger.info(f"Docker access confirmed. Server version: {stdout.strip()}")
                return True
            return False
        except SSHConnectionError:
            return False
    
    def get_docker_info(self) -> Dict[str, Any]:
        """
        Get Docker system information
        
        Returns:
            Dictionary containing Docker system info
        """
        try:
            exit_code, stdout, stderr = self.execute_docker_command("system info --format json")
            if exit_code == 0:
                import json
                return json.loads(stdout)
            else:
                logger.error(f"Failed to get Docker info: {stderr}")
                return {}
        except Exception as e:
            logger.error(f"Error getting Docker info: {str(e)}")
            return {}
    
    def check_service_health(self, port: int) -> bool:
        """
        Check if a service is responding on given port
        
        Args:
            port: Port number to check
            
        Returns:
            True if service is responding, False otherwise
        """
        try:
            command = f"timeout 5 bash -c '</dev/tcp/localhost/{port}' 2>/dev/null"
            exit_code, stdout, stderr = self.execute_command(command, timeout=10)
            return exit_code == 0
        except Exception:
            return False
    
    def get_container_logs(self, container_name: str, lines: int = 100) -> List[str]:
        """
        Get container logs
        
        Args:
            container_name: Name or ID of the container
            lines: Number of log lines to retrieve
            
        Returns:
            List of log lines
        """
        try:
            exit_code, stdout, stderr = self.execute_docker_command(
                f"logs --tail {lines} --timestamps {container_name}"
            )
            if exit_code == 0:
                return stdout.strip().split('\n') if stdout.strip() else []
            else:
                logger.error(f"Failed to get logs for {container_name}: {stderr}")
                return []
        except Exception as e:
            logger.error(f"Error getting logs for {container_name}: {str(e)}")
            return []
    
    @contextmanager
    def port_forward(self, local_port: int, remote_port: int, remote_host: str = 'localhost'):
        """
        Context manager for SSH port forwarding
        
        Args:
            local_port: Local port to bind to
            remote_port: Remote port to forward to
            remote_host: Remote host to forward to (default: localhost)
        """
        transport = None
        try:
            client = self._get_ssh_client()
            transport = client.get_transport()
            
            # Start port forwarding
            transport.request_port_forward('', local_port)
            logger.info(f"Port forwarding: localhost:{local_port} -> {remote_host}:{remote_port}")
            
            yield transport
            
        except Exception as e:
            logger.error(f"Port forwarding failed: {str(e)}")
            raise
        finally:
            if transport:
                try:
                    transport.cancel_port_forward('', local_port)
                except Exception:
                    pass
    
    def close(self) -> None:
        """Close SSH connection"""
        if self._client:
            try:
                self._client.close()
                logger.info("SSH connection closed")
            except Exception as e:
                logger.error(f"Error closing SSH connection: {str(e)}")
            finally:
                self._client = None
    
    def __del__(self):
        """Cleanup SSH connection on object destruction"""
        self.close()
