"""
Health check API endpoint
Provides application health status
"""

from flask import Blueprint, jsonify
import psutil
import os
from datetime import datetime

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Application health check endpoint
    Returns application status and basic metrics
    """
    try:
        # Get basic system info
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get application info
        process = psutil.Process()
        app_memory = process.memory_info()
        
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'uptime_seconds': int((datetime.now() - datetime.fromtimestamp(process.create_time())).total_seconds()),
            'system': {
                'cpu_percent': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent
                },
                'disk': {
                    'total': disk.total,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                }
            },
            'application': {
                'pid': process.pid,
                'memory_mb': app_memory.rss / 1024 / 1024,
                'threads': process.num_threads()
            },
            'services': {
                'ssh_service': check_ssh_service(),
                'monitoring_service': check_monitoring_service(),
                'docker_service': check_docker_service()
            }
        }
        
        return jsonify({
            'status': 'success',
            'data': health_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Health check failed: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

def check_ssh_service():
    """Check SSH service availability"""
    try:
        from app.services.ssh_service import SSHService
        ssh_service = SSHService()
        
        # Try a simple health check command
        result = ssh_service.execute_command('echo "health_check"', timeout=5)
        return {
            'status': 'healthy' if result['success'] else 'unhealthy',
            'message': result.get('output', result.get('error', 'Unknown'))[:100]
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': str(e)[:100]
        }

def check_monitoring_service():
    """Check Glances monitoring service availability"""
    try:
        import requests
        from flask import current_app
        
        # Get Glances config
        glances_host = current_app.config.get('GLANCES_HOST', 'logan-GL502VS')
        glances_port = current_app.config.get('GLANCES_PORT', 61208)
        glances_api_version = current_app.config.get('GLANCES_API_VERSION', '3')
        timeout = current_app.config.get('GLANCES_TIMEOUT', 5)
        
        # Test direct connection to Glances API
        url = f"http://{glances_host}:{glances_port}/api/{glances_api_version}/status"
        response = requests.get(url, timeout=timeout)
        
        if response.status_code == 200:
            return {
                'status': 'healthy',
                'message': f'Glances API accessible at {glances_host}:{glances_port}'
            }
        else:
            return {
                'status': 'unhealthy',
                'message': f'Glances API returned status {response.status_code}'
            }
            
    except requests.exceptions.ConnectionError:
        return {
            'status': 'unhealthy',
            'message': f'Cannot connect to Glances API at {glances_host}:{glances_port}'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': str(e)[:100]
        }

def check_docker_service():
    """Check Docker service availability"""
    try:
        from app.services.docker_service import DockerService
        docker_service = DockerService()
        
        # Try to list containers
        containers = docker_service.list_containers()
        return {
            'status': 'healthy' if containers is not None else 'unhealthy',
            'message': f'Found {len(containers) if containers else 0} containers'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': str(e)[:100]
        }
