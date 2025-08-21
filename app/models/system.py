"""System model for representing system metrics and information."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class SystemMetrics:
    """Model for system performance metrics."""
    
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_total: int
    disk_percent: float
    disk_used: int
    disk_total: int
    network_sent: int = 0
    network_received: int = 0
    load_average: List[float] = field(default_factory=list)
    uptime: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert system metrics to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'memory_used': self.memory_used,
            'memory_total': self.memory_total,
            'memory_used_gb': round(self.memory_used / (1024**3), 2),
            'memory_total_gb': round(self.memory_total / (1024**3), 2),
            'disk_percent': self.disk_percent,
            'disk_used': self.disk_used,
            'disk_total': self.disk_total,
            'disk_used_gb': round(self.disk_used / (1024**3), 2),
            'disk_total_gb': round(self.disk_total / (1024**3), 2),
            'network_sent': self.network_sent,
            'network_received': self.network_received,
            'load_average': self.load_average,
            'uptime': self.uptime,
            'uptime_formatted': self.format_uptime()
        }
    
    def format_uptime(self) -> str:
        """Format uptime in human readable format."""
        if not self.uptime:
            return "Unknown"
            
        days = int(self.uptime // 86400)
        hours = int((self.uptime % 86400) // 3600)
        minutes = int((self.uptime % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"


@dataclass
class ServiceHealth:
    """Model for service health check results."""
    
    service_name: str
    url: str
    status: str  # 'healthy', 'unhealthy', 'unknown'
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    last_checked: datetime = field(default_factory=datetime.now)
    
    @property
    def is_healthy(self) -> bool:
        """Check if service is healthy."""
        return self.status == 'healthy'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert service health to dictionary."""
        return {
            'service_name': self.service_name,
            'url': self.url,
            'status': self.status,
            'response_time': self.response_time,
            'status_code': self.status_code,
            'error_message': self.error_message,
            'last_checked': self.last_checked.isoformat(),
            'is_healthy': self.is_healthy
        }


@dataclass
class SystemInfo:
    """Model for general system information."""
    
    hostname: str
    platform: str
    architecture: str
    cpu_count: int
    cpu_model: str = ""
    total_memory: int = 0
    total_disk: int = 0
    docker_version: str = ""
    kernel_version: str = ""
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert system info to dictionary."""
        return {
            'hostname': self.hostname,
            'platform': self.platform,
            'architecture': self.architecture,
            'cpu_count': self.cpu_count,
            'cpu_model': self.cpu_model,
            'total_memory': self.total_memory,
            'total_memory_gb': round(self.total_memory / (1024**3), 2),
            'total_disk': self.total_disk,
            'total_disk_gb': round(self.total_disk / (1024**3), 2),
            'docker_version': self.docker_version,
            'kernel_version': self.kernel_version,
            'last_updated': self.last_updated.isoformat()
        }


@dataclass
class NetworkInfo:
    """Model for network interface information."""
    
    interface_name: str
    ip_address: str
    netmask: str = ""
    broadcast: str = ""
    mac_address: str = ""
    is_up: bool = True
    bytes_sent: int = 0
    bytes_recv: int = 0
    packets_sent: int = 0
    packets_recv: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert network info to dictionary."""
        return {
            'interface_name': self.interface_name,
            'ip_address': self.ip_address,
            'netmask': self.netmask,
            'broadcast': self.broadcast,
            'mac_address': self.mac_address,
            'is_up': self.is_up,
            'bytes_sent': self.bytes_sent,
            'bytes_recv': self.bytes_recv,
            'packets_sent': self.packets_sent,
            'packets_recv': self.packets_recv,
            'mb_sent': round(self.bytes_sent / (1024**2), 2),
            'mb_recv': round(self.bytes_recv / (1024**2), 2)
        }
