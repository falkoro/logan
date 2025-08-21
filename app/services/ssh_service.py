"""SSH service for remote Docker host management."""
import logging
import paramiko
from typing import Optional, Tuple, List, Dict, Any
from contextlib import contextmanager
import time
import os

logger = logging.getLogger(__name__)


class SSHService:
    """Service for managing SSH connections to remote Docker hosts."""
    
    def __init__(self, host: str, username: str, port: int = 22, 
                 key_path: Optional[str] = None, timeout: int = 30):
        """Initialize SSH service.
        
        Args:
            host: Remote host to connect to
            username: Username for SSH connection
            port: SSH port (default: 22)
            key_path: Path to SSH private key file
            timeout: Connection timeout in seconds
        """
        self.host = host
        self.username = username
        self.port = port
        self.key_path = key_path
        self.timeout = timeout
        self._client = None
        self._connected = False
        
    def connect(self) -> bool:
        """Establish SSH connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Set up authentication
            connect_kwargs = {
                'hostname': self.host,
                'username': self.username,
                'port': self.port,
                'timeout': self.timeout
            }
            
            if self.key_path and os.path.exists(self.key_path):
                logger.info(f"Using SSH key: {self.key_path}")
                connect_kwargs['key_filename'] = self.key_path
            else:
                logger.warning("No SSH key specified or key file not found, trying default keys")
            
            self._client.connect(**connect_kwargs)
            self._connected = True
            logger.info(f"SSH connection established to {self.username}@{self.host}:{self.port}")
            return True
            
        except paramiko.AuthenticationException as e:
            logger.error(f"SSH authentication failed: {e}")
            self._connected = False
            return False
        except paramiko.SSHException as e:
            logger.error(f"SSH connection failed: {e}")
            self._connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error during SSH connection: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Close SSH connection."""
        if self._client:
            self._client.close()
            self._connected = False
            logger.info("SSH connection closed")
    
    def is_connected(self) -> bool:
        """Check if SSH connection is active."""
        if not self._connected or not self._client:
            return False
        
        try:
            # Send a simple command to test connection
            transport = self._client.get_transport()
            if transport and transport.is_active():
                return True
        except Exception as e:
            logger.warning(f"SSH connection check failed: {e}")
        
        self._connected = False
        return False
    
    def execute_command(self, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """Execute a command on the remote host.
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        if not self.is_connected():
            logger.warning("SSH not connected, attempting to reconnect")
            if not self.connect():
                return -1, "", "SSH connection failed"
        
        try:
            logger.debug(f"Executing command: {command}")
            stdin, stdout, stderr = self._client.exec_command(command, timeout=timeout)
            
            # Read output
            stdout_data = stdout.read().decode('utf-8')
            stderr_data = stderr.read().decode('utf-8')
            exit_code = stdout.channel.recv_exit_status()
            
            logger.debug(f"Command exit code: {exit_code}")
            if stderr_data:
                logger.debug(f"Command stderr: {stderr_data[:500]}")
            
            return exit_code, stdout_data, stderr_data
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return -1, "", str(e)
    
    def execute_docker_command(self, docker_cmd: str, timeout: int = 30) -> Tuple[int, str, str]:
        """Execute a Docker command on the remote host.
        
        Args:
            docker_cmd: Docker command (without 'docker' prefix)
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        full_command = f"docker {docker_cmd}"
        return self.execute_command(full_command, timeout)
    
    def test_docker_access(self) -> bool:
        """Test if Docker is accessible on the remote host.
        
        Returns:
            bool: True if Docker is accessible, False otherwise
        """
        exit_code, stdout, stderr = self.execute_docker_command("version --format '{{.Server.Version}}'")
        if exit_code == 0 and stdout.strip():
            logger.info(f"Docker server version: {stdout.strip()}")
            return True
        else:
            logger.error(f"Docker access test failed: {stderr}")
            return False
    
    @contextmanager
    def ssh_connection(self):
        """Context manager for SSH connections."""
        if not self.is_connected():
            connected = self.connect()
            if not connected:
                raise ConnectionError("Failed to establish SSH connection")
        
        try:
            yield self
        finally:
            # Don't automatically disconnect in context manager
            # to allow connection reuse
            pass
    
    def get_file_content(self, remote_path: str) -> Optional[str]:
        """Get content of a remote file.
        
        Args:
            remote_path: Path to remote file
            
        Returns:
            str: File content or None if failed
        """
        if not self.is_connected():
            if not self.connect():
                return None
        
        try:
            sftp = self._client.open_sftp()
            with sftp.open(remote_path, 'r') as remote_file:
                content = remote_file.read().decode('utf-8')
            sftp.close()
            return content
        except Exception as e:
            logger.error(f"Failed to read remote file {remote_path}: {e}")
            return None
    
    def put_file_content(self, content: str, remote_path: str) -> bool:
        """Write content to a remote file.
        
        Args:
            content: Content to write
            remote_path: Path to remote file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected():
            if not self.connect():
                return False
        
        try:
            sftp = self._client.open_sftp()
            with sftp.open(remote_path, 'w') as remote_file:
                remote_file.write(content)
            sftp.close()
            return True
        except Exception as e:
            logger.error(f"Failed to write remote file {remote_path}: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        if not self.is_connected():
            self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
