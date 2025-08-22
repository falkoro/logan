"""
System monitoring model for representing system statistics
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

@dataclass
class CPUInfo:
    """CPU information and statistics"""
    percent: float = 0.0
    count_logical: int = 0
    count_physical: int = 0
    load_avg: List[float] = field(default_factory=list)
    frequency: float = 0.0

@dataclass
class MemoryInfo:
    """Memory information and statistics"""
    total: int = 0
    available: int = 0
    used: int = 0
    percent: float = 0.0
    swap_total: int = 0
    swap_used: int = 0
    swap_percent: float = 0.0
    
    @property
    def total_gb(self) -> float:
        """Get total memory in GB"""
        return self.total / (1024**3)
    
    @property
    def used_gb(self) -> float:
        """Get used memory in GB"""
        return self.used / (1024**3)
    
    @property
    def available_gb(self) -> float:
        """Get available memory in GB"""
        return self.available / (1024**3)

@dataclass
class DiskInfo:
    """Disk information and statistics"""
    path: str
    total: int = 0
    used: int = 0
    free: int = 0
    percent: float = 0.0
    
    @property
    def total_gb(self) -> float:
        """Get total disk space in GB"""
        return self.total / (1024**3)
    
    @property
    def used_gb(self) -> float:
        """Get used disk space in GB"""
        return self.used / (1024**3)
    
    @property
    def free_gb(self) -> float:
        """Get free disk space in GB"""
        return self.free / (1024**3)

@dataclass
class NetworkInterface:
    """Network interface information"""
    name: str
    bytes_sent: int = 0
    bytes_recv: int = 0
    packets_sent: int = 0
    packets_recv: int = 0
    errors_in: int = 0
    errors_out: int = 0
    drops_in: int = 0
    drops_out: int = 0
    is_up: bool = False
    speed: int = 0  # Mbps

@dataclass
class ProcessInfo:
    """Process information"""
    pid: int
    name: str
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_rss: int = 0
    status: str = "unknown"
    create_time: Optional[datetime] = None
    cmdline: List[str] = field(default_factory=list)

@dataclass
class SystemInfo:
    """Comprehensive system information"""
    hostname: str
    platform: str
    uptime: int = 0  # seconds
    boot_time: Optional[datetime] = None
    cpu: CPUInfo = field(default_factory=CPUInfo)
    memory: MemoryInfo = field(default_factory=MemoryInfo)
    disks: List[DiskInfo] = field(default_factory=list)
    networks: List[NetworkInterface] = field(default_factory=list)
    processes: List[ProcessInfo] = field(default_factory=list)
    temperature: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def uptime_formatted(self) -> str:
        """Get uptime as human readable string"""
        days, remainder = divmod(self.uptime, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    @property
    def total_disk_space_gb(self) -> float:
        """Get total disk space across all disks in GB"""
        return sum(disk.total_gb for disk in self.disks)
    
    @property
    def used_disk_space_gb(self) -> float:
        """Get used disk space across all disks in GB"""
        return sum(disk.used_gb for disk in self.disks)
    
    @property
    def disk_usage_percent(self) -> float:
        """Get overall disk usage percentage"""
        total = self.total_disk_space_gb
        if total == 0:
            return 0.0
        return (self.used_disk_space_gb / total) * 100
    
    @property
    def network_total_rx_mb(self) -> float:
        """Get total network bytes received in MB"""
        return sum(net.bytes_recv for net in self.networks) / (1024**2)
    
    @property
    def network_total_tx_mb(self) -> float:
        """Get total network bytes transmitted in MB"""
        return sum(net.bytes_sent for net in self.networks) / (1024**2)
    
    @classmethod
    def from_glances_dict(cls, glances_data: Dict[str, Any]) -> 'SystemInfo':
        """Create SystemInfo from Glances API response"""
        # Parse CPU information
        cpu_data = glances_data.get('cpu', {})
        cpu = CPUInfo(
            percent=cpu_data.get('total', 0.0),
            count_logical=glances_data.get('system', {}).get('cpucount', 0),
            load_avg=glances_data.get('load', {}).get('cpucore', [])
        )
        
        # Parse memory information
        mem_data = glances_data.get('mem', {})
        memory = MemoryInfo(
            total=mem_data.get('total', 0),
            available=mem_data.get('available', 0),
            used=mem_data.get('used', 0),
            percent=mem_data.get('percent', 0.0)
        )
        
        # Parse swap information
        swap_data = glances_data.get('memswap', {})
        memory.swap_total = swap_data.get('total', 0)
        memory.swap_used = swap_data.get('used', 0)
        memory.swap_percent = swap_data.get('percent', 0.0)
        
        # Parse disk information
        disks = []
        fs_data = glances_data.get('fs', [])
        for disk_data in fs_data:
            disks.append(DiskInfo(
                path=disk_data.get('mnt_point', '/'),
                total=disk_data.get('size', 0),
                used=disk_data.get('used', 0),
                free=disk_data.get('free', 0),
                percent=disk_data.get('percent', 0.0)
            ))
        
        # Parse network information
        networks = []
        net_data = glances_data.get('network', [])
        for net_info in net_data:
            networks.append(NetworkInterface(
                name=net_info.get('interface_name', 'unknown'),
                bytes_sent=net_info.get('tx', 0),
                bytes_recv=net_info.get('rx', 0),
                is_up=net_info.get('is_up', False)
            ))
        
        # Parse system information
        system_data = glances_data.get('system', {})
        uptime_data = glances_data.get('uptime', {})
        
        return cls(
            hostname=system_data.get('hostname', 'unknown'),
            platform=system_data.get('platform', 'unknown'),
            uptime=int(uptime_data.get('seconds', 0)),
            cpu=cpu,
            memory=memory,
            disks=disks,
            networks=networks,
            temperature=glances_data.get('sensors', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert SystemInfo to dictionary for API responses"""
        return {
            'hostname': self.hostname,
            'platform': self.platform,
            'uptime': self.uptime,
            'uptime_formatted': self.uptime_formatted,
            'timestamp': self.timestamp.isoformat(),
            'cpu': {
                'percent': self.cpu.percent,
                'count_logical': self.cpu.count_logical,
                'count_physical': self.cpu.count_physical,
                'load_avg': self.cpu.load_avg,
                'frequency': self.cpu.frequency
            },
            'memory': {
                'total': self.memory.total,
                'used': self.memory.used,
                'available': self.memory.available,
                'percent': self.memory.percent,
                'total_gb': self.memory.total_gb,
                'used_gb': self.memory.used_gb,
                'available_gb': self.memory.available_gb,
                'swap_total': self.memory.swap_total,
                'swap_used': self.memory.swap_used,
                'swap_percent': self.memory.swap_percent
            },
            'disks': [
                {
                    'path': disk.path,
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent,
                    'total_gb': disk.total_gb,
                    'used_gb': disk.used_gb,
                    'free_gb': disk.free_gb
                } for disk in self.disks
            ],
            'networks': [
                {
                    'name': net.name,
                    'bytes_sent': net.bytes_sent,
                    'bytes_recv': net.bytes_recv,
                    'is_up': net.is_up,
                    'speed': net.speed
                } for net in self.networks
            ],
            'temperature': self.temperature,
            'summary': {
                'total_disk_space_gb': self.total_disk_space_gb,
                'used_disk_space_gb': self.used_disk_space_gb,
                'disk_usage_percent': self.disk_usage_percent,
                'network_total_rx_mb': self.network_total_rx_mb,
                'network_total_tx_mb': self.network_total_tx_mb
            }
        }
