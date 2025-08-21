"""Container model for representing Docker containers."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class ContainerModel:
    """Model representing a Docker container."""
    
    id: str
    name: str
    image: str
    status: str
    state: str
    created: datetime
    ports: Dict[str, List[Dict[str, str]]] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    networks: Dict[str, Any] = field(default_factory=dict)
    mounts: List[Dict[str, str]] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    
    # Service-specific information
    service_name: Optional[str] = None
    service_port: Optional[int] = None
    service_category: Optional[str] = None
    vpn_required: bool = False
    health_status: Optional[str] = None
    
    @property
    def is_running(self) -> bool:
        """Check if container is running."""
        return self.state.lower() == 'running'
    
    @property
    def main_port(self) -> Optional[int]:
        """Get the main exposed port for this container."""
        if self.service_port:
            return self.service_port
            
        # Try to extract from ports mapping
        for container_port, host_mappings in self.ports.items():
            if host_mappings:
                try:
                    return int(host_mappings[0].get('HostPort', 0))
                except (ValueError, KeyError):
                    continue
        return None
    
    @property
    def web_url(self) -> Optional[str]:
        """Get the web URL for this service if applicable."""
        if self.main_port:
            return f"http://logan-GL502VS:{self.main_port}"
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert container model to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'image': self.image,
            'status': self.status,
            'state': self.state,
            'created': self.created.isoformat() if self.created else None,
            'ports': self.ports,
            'labels': self.labels,
            'networks': self.networks,
            'mounts': self.mounts,
            'environment': self.environment,
            'service_name': self.service_name,
            'service_port': self.service_port,
            'service_category': self.service_category,
            'vpn_required': self.vpn_required,
            'health_status': self.health_status,
            'is_running': self.is_running,
            'main_port': self.main_port,
            'web_url': self.web_url
        }
    
    @classmethod
    def from_docker_container(cls, container_data: Dict[str, Any], service_config: Dict[str, Any] = None) -> 'ContainerModel':
        """Create ContainerModel from Docker API response."""
        # Extract basic container information
        container_id = container_data.get('Id', '')
        name = container_data.get('Name', '').lstrip('/')
        image = container_data.get('Config', {}).get('Image', '')
        status = container_data.get('State', {}).get('Status', 'unknown')
        state = container_data.get('State', {}).get('Status', 'unknown')
        
        # Parse creation time
        created_str = container_data.get('Created', '')
        created = None
        if created_str:
            try:
                created = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
            except ValueError:
                created = datetime.now()
        
        # Extract port mappings
        ports = {}
        network_settings = container_data.get('NetworkSettings', {})
        port_bindings = network_settings.get('Ports', {})
        if port_bindings:
            ports = port_bindings
        
        # Extract labels
        labels = container_data.get('Config', {}).get('Labels') or {}
        
        # Extract networks
        networks = network_settings.get('Networks', {})
        
        # Extract mounts
        mounts = container_data.get('Mounts', [])
        
        # Extract environment variables
        env_list = container_data.get('Config', {}).get('Env', [])
        environment = {}
        for env_var in env_list:
            if '=' in env_var:
                key, value = env_var.split('=', 1)
                environment[key] = value
        
        # Add service-specific information if provided
        service_name = None
        service_port = None
        service_category = None
        vpn_required = False
        
        if service_config:
            service_name = service_config.get('name')
            service_port = service_config.get('port')
            service_category = service_config.get('category')
            vpn_required = service_config.get('vpn_required', False)
        
        # Try to determine health status
        health_status = None
        health_data = container_data.get('State', {}).get('Health')
        if health_data:
            health_status = health_data.get('Status', 'unknown')
        
        return cls(
            id=container_id,
            name=name,
            image=image,
            status=status,
            state=state,
            created=created,
            ports=ports,
            labels=labels,
            networks=networks,
            mounts=mounts,
            environment=environment,
            service_name=service_name,
            service_port=service_port,
            service_category=service_category,
            vpn_required=vpn_required,
            health_status=health_status
        )
