"""Monitoring service for system metrics and service health checks."""
import logging
import requests
import psutil
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import time

from ..models.system import SystemMetrics, ServiceHealth, SystemInfo, NetworkInfo
from .ssh_service import SSHService

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service for monitoring system metrics and service health."""
    
    def __init__(self, ssh_service: SSHService, managed_services: Dict[str, Any]):
        """Initialize monitoring service.
        
        Args:
            ssh_service: SSH service for remote connections
            managed_services: Dictionary of managed services configuration
        """
        self.ssh = ssh_service
        self.managed_services = managed_services
        self._metrics_cache = []
        self._health_cache = {}
        self._cache_ttl = 60  # Cache TTL in seconds
        self._last_metrics_update = None
        self._last_health_update = None
    
    def get_system_metrics(self, use_cache: bool = True) -> Optional[SystemMetrics]:
        """Get current system metrics from remote host.
        
        Args:
            use_cache: Whether to use cached metrics if available
            
        Returns:
            SystemMetrics object or None if failed
        """
        now = datetime.now()
        
        # Check cache
        if (use_cache and self._last_metrics_update and 
            (now - self._last_metrics_update).seconds < self._cache_ttl and
            self._metrics_cache):
            return self._metrics_cache[-1]
        
        try:
            # Get system metrics via SSH commands
            metrics_data = {}
            
            # CPU usage
            exit_code, stdout, stderr = self.ssh.execute_command(
                "grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$3+$4)} END {print usage}'"
            )
            if exit_code == 0 and stdout.strip():
                try:
                    metrics_data['cpu_percent'] = float(stdout.strip())
                except ValueError:
                    metrics_data['cpu_percent'] = 0.0
            else:
                metrics_data['cpu_percent'] = 0.0
            
            # Memory usage
            exit_code, stdout, stderr = self.ssh.execute_command("free -b | grep '^Mem'")
            if exit_code == 0 and stdout.strip():
                parts = stdout.strip().split()
                if len(parts) >= 3:
                    total = int(parts[1])
                    used = int(parts[2])
                    metrics_data['memory_total'] = total
                    metrics_data['memory_used'] = used
                    metrics_data['memory_percent'] = (used / total) * 100 if total > 0 else 0
            
            if 'memory_total' not in metrics_data:
                metrics_data['memory_total'] = 0
                metrics_data['memory_used'] = 0
                metrics_data['memory_percent'] = 0
            
            # Disk usage
            exit_code, stdout, stderr = self.ssh.execute_command("df -B1 / | tail -1")
            if exit_code == 0 and stdout.strip():
                parts = stdout.strip().split()
                if len(parts) >= 4:
                    total = int(parts[1])
                    used = int(parts[2])
                    metrics_data['disk_total'] = total
                    metrics_data['disk_used'] = used
                    metrics_data['disk_percent'] = (used / total) * 100 if total > 0 else 0
            
            if 'disk_total' not in metrics_data:
                metrics_data['disk_total'] = 0
                metrics_data['disk_used'] = 0
                metrics_data['disk_percent'] = 0
            
            # Load average
            exit_code, stdout, stderr = self.ssh.execute_command("cat /proc/loadavg")
            if exit_code == 0 and stdout.strip():
                parts = stdout.strip().split()
                if len(parts) >= 3:
                    metrics_data['load_average'] = [float(parts[0]), float(parts[1]), float(parts[2])]
                else:
                    metrics_data['load_average'] = []
            else:
                metrics_data['load_average'] = []
            
            # Uptime
            exit_code, stdout, stderr = self.ssh.execute_command("cat /proc/uptime")
            if exit_code == 0 and stdout.strip():
                parts = stdout.strip().split()
                if parts:
                    metrics_data['uptime'] = float(parts[0])
                else:
                    metrics_data['uptime'] = 0.0
            else:
                metrics_data['uptime'] = 0.0
            
            # Network stats (simplified)
            metrics_data['network_sent'] = 0
            metrics_data['network_received'] = 0
            
            # Create SystemMetrics object
            metrics = SystemMetrics(
                timestamp=now,
                cpu_percent=metrics_data['cpu_percent'],
                memory_percent=metrics_data['memory_percent'],
                memory_used=metrics_data['memory_used'],
                memory_total=metrics_data['memory_total'],
                disk_percent=metrics_data['disk_percent'],
                disk_used=metrics_data['disk_used'],
                disk_total=metrics_data['disk_total'],
                network_sent=metrics_data['network_sent'],
                network_received=metrics_data['network_received'],
                load_average=metrics_data['load_average'],
                uptime=metrics_data['uptime']
            )
            
            # Update cache
            self._metrics_cache.append(metrics)
            self._last_metrics_update = now
            
            # Keep only last 24 hours of metrics
            cutoff_time = now - timedelta(hours=24)
            self._metrics_cache = [m for m in self._metrics_cache if m.timestamp > cutoff_time]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return None
    
    def get_service_health_status(self, use_cache: bool = True) -> List[ServiceHealth]:
        """Get health status of all managed services.
        
        Args:
            use_cache: Whether to use cached health data if available
            
        Returns:
            List of ServiceHealth objects
        """
        now = datetime.now()
        
        # Check cache
        if (use_cache and self._last_health_update and 
            (now - self._last_health_update).seconds < self._cache_ttl and
            self._health_cache):
            return list(self._health_cache.values())
        
        health_results = []
        
        for service_key, service_config in self.managed_services.items():
            service_name = service_config.get('name', service_key)
            port = service_config.get('port')
            
            if not port:
                continue
            
            url = f"http://{self.ssh.host}:{port}"
            health_status = self._check_service_health(service_name, url)
            health_results.append(health_status)
            self._health_cache[service_key] = health_status
        
        self._last_health_update = now
        return health_results
    
    def _check_service_health(self, service_name: str, url: str, timeout: int = 5) -> ServiceHealth:
        """Check health of a single service.
        
        Args:
            service_name: Name of the service
            url: URL to check
            timeout: Request timeout in seconds
            
        Returns:
            ServiceHealth object
        """
        start_time = time.time()
        
        try:
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                status = 'healthy'
                error_message = None
            elif 300 <= response.status_code < 400:
                # Redirects are OK for web services
                status = 'healthy'
                error_message = None
            else:
                status = 'unhealthy'
                error_message = f"HTTP {response.status_code}"
            
            return ServiceHealth(
                service_name=service_name,
                url=url,
                status=status,
                response_time=response_time,
                status_code=response.status_code,
                error_message=error_message
            )
            
        except requests.exceptions.ConnectTimeout:
            return ServiceHealth(
                service_name=service_name,
                url=url,
                status='unhealthy',
                response_time=timeout,
                error_message='Connection timeout'
            )
        except requests.exceptions.ConnectionError:
            return ServiceHealth(
                service_name=service_name,
                url=url,
                status='unhealthy',
                error_message='Connection refused'
            )
        except requests.exceptions.RequestException as e:
            return ServiceHealth(
                service_name=service_name,
                url=url,
                status='unhealthy',
                error_message=str(e)
            )
        except Exception as e:
            return ServiceHealth(
                service_name=service_name,
                url=url,
                status='unknown',
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def get_system_info(self) -> Optional[SystemInfo]:
        """Get general system information from remote host.
        
        Returns:
            SystemInfo object or None if failed
        """
        try:
            system_data = {}
            
            # Hostname
            exit_code, stdout, stderr = self.ssh.execute_command("hostname")
            system_data['hostname'] = stdout.strip() if exit_code == 0 else 'Unknown'
            
            # Platform info
            exit_code, stdout, stderr = self.ssh.execute_command("uname -s")
            system_data['platform'] = stdout.strip() if exit_code == 0 else 'Unknown'
            
            # Architecture
            exit_code, stdout, stderr = self.ssh.execute_command("uname -m")
            system_data['architecture'] = stdout.strip() if exit_code == 0 else 'Unknown'
            
            # CPU count
            exit_code, stdout, stderr = self.ssh.execute_command("nproc")
            if exit_code == 0 and stdout.strip().isdigit():
                system_data['cpu_count'] = int(stdout.strip())
            else:
                system_data['cpu_count'] = 1
            
            # CPU model
            exit_code, stdout, stderr = self.ssh.execute_command("grep 'model name' /proc/cpuinfo | head -1 | cut -d ':' -f 2")
            system_data['cpu_model'] = stdout.strip() if exit_code == 0 else 'Unknown'
            
            # Total memory
            exit_code, stdout, stderr = self.ssh.execute_command("grep MemTotal /proc/meminfo | awk '{print $2 * 1024}'")
            if exit_code == 0 and stdout.strip().isdigit():
                system_data['total_memory'] = int(stdout.strip())
            else:
                system_data['total_memory'] = 0
            
            # Total disk space
            exit_code, stdout, stderr = self.ssh.execute_command("df -B1 / | tail -1 | awk '{print $2}'")
            if exit_code == 0 and stdout.strip().isdigit():
                system_data['total_disk'] = int(stdout.strip())
            else:
                system_data['total_disk'] = 0
            
            # Docker version
            exit_code, stdout, stderr = self.ssh.execute_docker_command("version --format '{{.Server.Version}}'")
            system_data['docker_version'] = stdout.strip() if exit_code == 0 else 'Unknown'
            
            # Kernel version
            exit_code, stdout, stderr = self.ssh.execute_command("uname -r")
            system_data['kernel_version'] = stdout.strip() if exit_code == 0 else 'Unknown'
            
            return SystemInfo(
                hostname=system_data['hostname'],
                platform=system_data['platform'],
                architecture=system_data['architecture'],
                cpu_count=system_data['cpu_count'],
                cpu_model=system_data['cpu_model'],
                total_memory=system_data['total_memory'],
                total_disk=system_data['total_disk'],
                docker_version=system_data['docker_version'],
                kernel_version=system_data['kernel_version']
            )
            
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return None
    
    def get_network_info(self) -> List[NetworkInfo]:
        """Get network interface information from remote host.
        
        Returns:
            List of NetworkInfo objects
        """
        try:
            interfaces = []
            
            # Get interface information
            exit_code, stdout, stderr = self.ssh.execute_command("ip -j addr show")
            
            if exit_code == 0 and stdout.strip():
                try:
                    interface_data = json.loads(stdout)
                    
                    for iface in interface_data:
                        name = iface.get('ifname', 'unknown')
                        
                        # Skip loopback and docker interfaces for simplicity
                        if name.startswith(('lo', 'docker', 'br-')):
                            continue
                        
                        # Extract IP addresses
                        ip_address = ''
                        for addr_info in iface.get('addr_info', []):
                            if addr_info.get('family') == 'inet':  # IPv4
                                ip_address = addr_info.get('local', '')
                                break
                        
                        if ip_address:
                            interfaces.append(NetworkInfo(
                                interface_name=name,
                                ip_address=ip_address,
                                is_up='UP' in iface.get('flags', [])
                            ))
                
                except json.JSONDecodeError:
                    logger.error("Failed to parse network interface JSON")
            
            return interfaces
            
        except Exception as e:
            logger.error(f"Error getting network info: {e}")
            return []
    
    def get_historical_metrics(self, hours: int = 24) -> List[SystemMetrics]:
        """Get historical system metrics.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of SystemMetrics objects
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [m for m in self._metrics_cache if m.timestamp > cutoff_time]
    
    def clear_cache(self):
        """Clear all cached data."""
        self._metrics_cache.clear()
        self._health_cache.clear()
        self._last_metrics_update = None
        self._last_health_update = None
