"""
Monitoring Service for system metrics via Glances API
"""
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin
from app.models.system import SystemInfo
from app.config.settings import Config

logger = logging.getLogger(__name__)

class MonitoringServiceError(Exception):
    """Monitoring service related errors"""
    pass

class MonitoringService:
    """Service for collecting system monitoring data via Glances API"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_url = f"http://{config.GLANCES_HOST}:{config.GLANCES_PORT}"
        self.api_version = config.GLANCES_API_VERSION
        self.timeout = config.GLANCES_TIMEOUT
        self._session = requests.Session()
        self._session.timeout = self.timeout
        
        # Set up session headers
        self._session.headers.update({
            'User-Agent': 'Docker-Dashboard/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, endpoint: str) -> Dict[str, Any]:
        """
        Make HTTP request to Glances API
        
        Args:
            endpoint: API endpoint to call
            
        Returns:
            JSON response data
            
        Raises:
            MonitoringServiceError: If request fails
        """
        url = urljoin(self.base_url, f"/api/{self.api_version}/{endpoint}")
        
        try:
            response = self._session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.ConnectionError:
            raise MonitoringServiceError(f"Cannot connect to Glances API at {self.base_url}")
        except requests.exceptions.Timeout:
            raise MonitoringServiceError(f"Timeout connecting to Glances API")
        except requests.exceptions.HTTPError as e:
            raise MonitoringServiceError(f"HTTP error from Glances API: {e}")
        except json.JSONDecodeError:
            raise MonitoringServiceError("Invalid JSON response from Glances API")
        except Exception as e:
            raise MonitoringServiceError(f"Unexpected error calling Glances API: {e}")
    
    def test_connection(self) -> bool:
        """
        Test connection to Glances API
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            data = self._make_request("status")
            return isinstance(data, dict)
        except MonitoringServiceError:
            return False
    
    def get_system_info(self) -> Optional[SystemInfo]:
        """
        Get comprehensive system information
        
        Returns:
            SystemInfo object or None if failed
        """
        try:
            # Get all system data in one call
            all_data = self._make_request("all")
            
            if not all_data:
                logger.warning("No data returned from Glances API")
                return None
            
            return SystemInfo.from_glances_dict(all_data)
            
        except MonitoringServiceError as e:
            logger.error(f"Failed to get system info: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting system info: {e}")
            return None
    
    def get_cpu_info(self) -> Optional[Dict[str, Any]]:
        """
        Get CPU information and statistics
        
        Returns:
            Dictionary with CPU data or None if failed
        """
        try:
            return self._make_request("cpu")
        except MonitoringServiceError as e:
            logger.error(f"Failed to get CPU info: {e}")
            return None
    
    def get_memory_info(self) -> Optional[Dict[str, Any]]:
        """
        Get memory information and statistics
        
        Returns:
            Dictionary with memory data or None if failed
        """
        try:
            return self._make_request("mem")
        except MonitoringServiceError as e:
            logger.error(f"Failed to get memory info: {e}")
            return None
    
    def get_disk_info(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get disk information and statistics
        
        Returns:
            List of dictionaries with disk data or None if failed
        """
        try:
            return self._make_request("fs")
        except MonitoringServiceError as e:
            logger.error(f"Failed to get disk info: {e}")
            return None
    
    def get_network_info(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get network interface information and statistics
        
        Returns:
            List of dictionaries with network data or None if failed
        """
        try:
            return self._make_request("network")
        except MonitoringServiceError as e:
            logger.error(f"Failed to get network info: {e}")
            return None
    
    def get_process_info(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get running process information
        
        Returns:
            List of dictionaries with process data or None if failed
        """
        try:
            return self._make_request("processlist")
        except MonitoringServiceError as e:
            logger.error(f"Failed to get process info: {e}")
            return None
    
    def get_docker_info(self) -> Optional[Dict[str, Any]]:
        """
        Get Docker container information from Glances
        
        Returns:
            Dictionary with Docker data or None if failed
        """
        try:
            return self._make_request("docker")
        except MonitoringServiceError as e:
            logger.error(f"Failed to get Docker info from Glances: {e}")
            return None
    
    def get_sensors_info(self) -> Optional[Dict[str, Any]]:
        """
        Get temperature and sensor information
        
        Returns:
            Dictionary with sensor data or None if failed
        """
        try:
            return self._make_request("sensors")
        except MonitoringServiceError as e:
            logger.error(f"Failed to get sensors info: {e}")
            return None
    
    def get_uptime_info(self) -> Optional[Dict[str, Any]]:
        """
        Get system uptime information
        
        Returns:
            Dictionary with uptime data or None if failed
        """
        try:
            return self._make_request("uptime")
        except MonitoringServiceError as e:
            logger.error(f"Failed to get uptime info: {e}")
            return None
    
    def get_system_load(self) -> Optional[Dict[str, Any]]:
        """
        Get system load average information
        
        Returns:
            Dictionary with load data or None if failed
        """
        try:
            return self._make_request("load")
        except MonitoringServiceError as e:
            logger.error(f"Failed to get system load: {e}")
            return None
    
    def get_alert_info(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get system alerts from Glances
        
        Returns:
            List of dictionaries with alert data or None if failed
        """
        try:
            return self._make_request("alert")
        except MonitoringServiceError as e:
            logger.error(f"Failed to get alerts: {e}")
            return None
    
    def get_plugin_list(self) -> Optional[List[str]]:
        """
        Get list of available Glances plugins
        
        Returns:
            List of plugin names or None if failed
        """
        try:
            return self._make_request("pluginslist")
        except MonitoringServiceError as e:
            logger.error(f"Failed to get plugins list: {e}")
            return None
    
    def get_historical_data(self, plugin: str, nb: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        Get historical data for a specific plugin
        
        Args:
            plugin: Plugin name (e.g., 'cpu', 'mem', 'load')
            nb: Number of historical entries to retrieve
            
        Returns:
            List of historical data entries or None if failed
        """
        try:
            return self._make_request(f"{plugin}/history/{nb}")
        except MonitoringServiceError as e:
            logger.error(f"Failed to get historical data for {plugin}: {e}")
            return None
    
    def get_system_summary(self) -> Dict[str, Any]:
        """
        Get a summary of key system metrics
        
        Returns:
            Dictionary with summarized system metrics
        """
        summary = {
            'timestamp': datetime.now().isoformat(),
            'status': 'unknown',
            'cpu_percent': 0.0,
            'memory_percent': 0.0,
            'disk_percent': 0.0,
            'uptime': 'unknown',
            'alerts': 0,
            'processes': 0
        }
        
        try:
            system_info = self.get_system_info()
            if system_info:
                summary.update({
                    'status': 'healthy',
                    'cpu_percent': system_info.cpu.percent,
                    'memory_percent': system_info.memory.percent,
                    'disk_percent': system_info.disk_usage_percent,
                    'uptime': system_info.uptime_formatted,
                    'processes': len(system_info.processes)
                })
            
            # Get alerts
            alerts = self.get_alert_info()
            if alerts:
                summary['alerts'] = len(alerts)
            
        except Exception as e:
            logger.error(f"Error getting system summary: {e}")
            summary['status'] = 'error'
        
        return summary
    
    def close(self):
        """Close the HTTP session"""
        try:
            self._session.close()
        except Exception as e:
            logger.error(f"Error closing monitoring service session: {e}")
    
    def __del__(self):
        """Cleanup on object destruction"""
        self.close()
