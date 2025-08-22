"""
Container model for representing Docker containers
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

class ContainerStatus(Enum):
    """Container status enumeration"""
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    RESTARTING = "restarting"
    ERROR = "error"
    UNKNOWN = "unknown"

@dataclass
class ContainerPort:
    """Represents a container port mapping"""
    container_port: int
    host_port: int
    protocol: str = "tcp"
    host_ip: str = "0.0.0.0"

@dataclass
class ContainerStats:
    """Container resource statistics"""
    cpu_percent: float = 0.0
    memory_usage: int = 0
    memory_limit: int = 0
    memory_percent: float = 0.0
    network_rx: int = 0
    network_tx: int = 0
    disk_read: int = 0
    disk_write: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class Container:
    """Docker container representation"""
    id: str
    name: str
    image: str
    status: ContainerStatus
    created: datetime
    started: Optional[datetime] = None
    ports: List[ContainerPort] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    command: str = ""
    size: str = ""
    networks: List[str] = field(default_factory=list)
    # Additional computed properties for the frontend
    is_running: bool = field(default=False)
    is_healthy: bool = field(default=True)
    health_status: Optional[str] = None
    restart_policy: str = "no"
    stats: Optional[ContainerStats] = None
    logs_tail: List[str] = field(default_factory=list)
    health_status: Optional[str] = None
    restart_policy: str = "no"
    stats: Optional[ContainerStats] = None
    logs_tail: List[str] = field(default_factory=list)
    
    @property
    def is_running(self) -> bool:
        """Check if container is running"""
        return self.status == ContainerStatus.RUNNING
    
    @property
    def is_healthy(self) -> bool:
        """Check if container is healthy"""
        if self.health_status is None:
            return self.is_running
        return self.health_status == "healthy"
    
    @property
    def uptime(self) -> Optional[str]:
        """Get container uptime as human readable string"""
        if not self.started or not self.is_running:
            return None
        
        # Use timezone-aware datetime for comparison
        now = datetime.now(timezone.utc)
        # Ensure both datetimes are timezone-aware
        started = self.started
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        
        delta = now - started
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    @property
    def memory_usage_mb(self) -> float:
        """Get memory usage in MB"""
        if self.stats:
            return self.stats.memory_usage / (1024 * 1024)
        return 0.0
    
    @property
    def primary_port(self) -> Optional[int]:
        """Get the primary exposed port"""
        if not self.ports:
            return None
        return min(port.host_port for port in self.ports)
    
    @classmethod
    def from_docker_dict(cls, docker_dict: Dict[str, Any]) -> 'Container':
        """Create Container instance from Docker API response"""
        # Parse container status
        state = docker_dict.get('State', {})
        status_map = {
            'running': ContainerStatus.RUNNING,
            'exited': ContainerStatus.STOPPED,
            'paused': ContainerStatus.PAUSED,
            'restarting': ContainerStatus.RESTARTING,
            'dead': ContainerStatus.ERROR,
        }
        status = status_map.get(state.get('Status', '').lower(), ContainerStatus.UNKNOWN)
        
        # Parse ports
        ports = []
        port_bindings = docker_dict.get('HostConfig', {}).get('PortBindings') or {}
        for container_port, bindings in port_bindings.items():
            if bindings:
                for binding in bindings:
                    port_info = container_port.split('/')
                    ports.append(ContainerPort(
                        container_port=int(port_info[0]),
                        host_port=int(binding['HostPort']),
                        protocol=port_info[1] if len(port_info) > 1 else 'tcp',
                        host_ip=binding.get('HostIp', '0.0.0.0')
                    ))
        
        # Parse dates
        created = datetime.fromisoformat(docker_dict['Created'].replace('Z', '+00:00'))
        started = None
        if state.get('StartedAt') and state['StartedAt'] != '0001-01-01T00:00:00Z':
            started = datetime.fromisoformat(state['StartedAt'].replace('Z', '+00:00'))
        
        return cls(
            id=docker_dict['Id'][:12],  # Short ID
            name=docker_dict['Name'].lstrip('/'),
            image=docker_dict['Config']['Image'],
            status=status,
            created=created,
            started=started,
            ports=ports,
            environment=dict(env.split('=', 1) for env in docker_dict.get('Config', {}).get('Env', []) if '=' in env),
            labels=docker_dict.get('Config', {}).get('Labels') or {},
            health_status=state.get('Health', {}).get('Status'),
            restart_policy=docker_dict.get('HostConfig', {}).get('RestartPolicy', {}).get('Name', 'no'),
            is_running=status == ContainerStatus.RUNNING,
            is_healthy=state.get('Health', {}).get('Status') != 'unhealthy' if state.get('Health') else True
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert container to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'image': self.image,
            'status': self.status.value,
            'created': self.created.isoformat(),
            'started': self.started.isoformat() if self.started else None,
            'ports': [f"{p.host_ip}:{p.host_port}→{p.container_port}/{p.protocol}" for p in self.ports] if self.ports else [],
            'health_status': self.health_status,
            'is_running': self.is_running,
            'is_healthy': self.is_healthy,
            'uptime': self.uptime,
            'primary_port': self.primary_port,
            'restart_policy': self.restart_policy,
            'command': self.command,
            'size': self.size,
            'networks': self.networks,
            'stats': {
                'cpu_percent': self.stats.cpu_percent,
                'memory_usage_mb': self.memory_usage_mb,
                'memory_percent': self.stats.memory_percent,
                'network_rx': self.stats.network_rx,
                'network_tx': self.stats.network_tx
            } if self.stats else None
        }
