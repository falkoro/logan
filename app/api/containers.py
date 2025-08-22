"""
Container API endpoints
"""
import logging
from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any
from app.services import DockerService, DockerServiceError

logger = logging.getLogger(__name__)

containers_bp = Blueprint('containers', __name__, url_prefix='/api/containers')

def get_docker_service() -> DockerService:
    """Get Docker service instance from app context"""
    return current_app.docker_service

@containers_bp.route('/', methods=['GET'])
def list_containers():
    """List all containers"""
    try:
        include_stopped = request.args.get('include_stopped', 'true').lower() == 'true'
        quick = request.args.get('quick', 'false').lower() == 'true'  # Quick mode for basic info only
        docker_service = get_docker_service()
        containers = docker_service.list_containers(include_stopped=include_stopped, quick_mode=quick)
        
        return jsonify({
            'success': True,
            'data': [container.to_dict() for container in containers],
            'count': len(containers)
        })
        
    except DockerServiceError as e:
        logger.error(f"Docker service error listing containers: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error listing containers: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@containers_bp.route('/overview', methods=['GET'])
def containers_overview():
    """Get quick overview of containers without detailed stats"""
    try:
        docker_service = get_docker_service()
        containers = docker_service.list_containers(include_stopped=True, quick_mode=True)
        
        # Calculate summary stats
        total = len(containers)
        running = sum(1 for c in containers if c.is_running)
        stopped = total - running
        
        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'running': running,
                'stopped': stopped,
                'containers': [container.to_dict() for container in containers]
            }
        })
        
    except DockerServiceError as e:
        logger.error(f"Docker service error getting containers overview: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error getting containers overview: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@containers_bp.route('/<container_name>', methods=['GET'])
def get_container(container_name: str):
    """Get details for a specific container"""
    try:
        docker_service = get_docker_service()
        container = docker_service.get_container_details(container_name)
        
        if container is None:
            return jsonify({
                'success': False,
                'error': f'Container {container_name} not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': container.to_dict()
        })
        
    except DockerServiceError as e:
        logger.error(f"Docker service error getting container {container_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error getting container {container_name}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@containers_bp.route('/<container_name>/start', methods=['POST'])
def start_container(container_name: str):
    """Start a container"""
    try:
        docker_service = get_docker_service()
        success = docker_service.start_container(container_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Container {container_name} started successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to start container {container_name}'
            }), 500
            
    except DockerServiceError as e:
        logger.error(f"Docker service error starting container {container_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error starting container {container_name}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@containers_bp.route('/<container_name>/stop', methods=['POST'])
def stop_container(container_name: str):
    """Stop a container"""
    try:
        timeout = request.json.get('timeout', 10) if request.is_json else 10
        docker_service = get_docker_service()
        success = docker_service.stop_container(container_name, timeout=timeout)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Container {container_name} stopped successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to stop container {container_name}'
            }), 500
            
    except DockerServiceError as e:
        logger.error(f"Docker service error stopping container {container_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error stopping container {container_name}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@containers_bp.route('/<container_name>/restart', methods=['POST'])
def restart_container(container_name: str):
    """Restart a container"""
    try:
        timeout = request.json.get('timeout', 10) if request.is_json else 10
        docker_service = get_docker_service()
        success = docker_service.restart_container(container_name, timeout=timeout)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Container {container_name} restarted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to restart container {container_name}'
            }), 500
            
    except DockerServiceError as e:
        logger.error(f"Docker service error restarting container {container_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error restarting container {container_name}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@containers_bp.route('/<container_name>/logs', methods=['GET'])
def get_container_logs(container_name: str):
    """Get container logs"""
    try:
        lines = int(request.args.get('lines', 100))
        docker_service = get_docker_service()
        logs = docker_service.get_container_logs(container_name, lines=lines)
        
        return jsonify({
            'success': True,
            'data': {
                'container': container_name,
                'logs': logs,
                'lines': len(logs)
            }
        })
        
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Invalid lines parameter, must be integer'
        }), 400
    except DockerServiceError as e:
        logger.error(f"Docker service error getting logs for {container_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error getting logs for {container_name}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@containers_bp.route('/<container_name>/stats', methods=['GET'])
def get_container_stats(container_name: str):
    """Get container resource statistics"""
    try:
        docker_service = get_docker_service()
        stats = docker_service.get_container_stats(container_name)
        
        if stats is None:
            return jsonify({
                'success': False,
                'error': f'Stats not available for container {container_name}'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'container': container_name,
                'cpu_percent': stats.cpu_percent,
                'memory_usage': stats.memory_usage,
                'memory_limit': stats.memory_limit,
                'memory_percent': stats.memory_percent,
                'memory_usage_mb': stats.memory_usage / (1024 * 1024),
                'network_rx': stats.network_rx,
                'network_tx': stats.network_tx,
                'timestamp': stats.timestamp.isoformat()
            }
        })
        
    except DockerServiceError as e:
        logger.error(f"Docker service error getting stats for {container_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error getting stats for {container_name}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@containers_bp.route('/<container_name>/health', methods=['GET'])
def check_container_health(container_name: str):
    """Check container health status"""
    try:
        docker_service = get_docker_service()
        health = docker_service.check_container_health(container_name)
        
        if health is None:
            return jsonify({
                'success': False,
                'error': f'Container {container_name} not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': health
        })
        
    except DockerServiceError as e:
        logger.error(f"Docker service error checking health for {container_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error checking health for {container_name}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@containers_bp.route('/bulk/action', methods=['POST'])
def bulk_container_action():
    """Perform bulk action on multiple containers"""
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Request must be JSON'
            }), 400
        
        data = request.get_json()
        action = data.get('action')
        container_names = data.get('containers', [])
        timeout = data.get('timeout', 10)
        
        if action not in ['start', 'stop', 'restart']:
            return jsonify({
                'success': False,
                'error': 'Invalid action. Must be one of: start, stop, restart'
            }), 400
        
        if not container_names:
            return jsonify({
                'success': False,
                'error': 'No containers specified'
            }), 400
        
        docker_service = get_docker_service()
        results = {}
        
        for container_name in container_names:
            try:
                if action == 'start':
                    success = docker_service.start_container(container_name)
                elif action == 'stop':
                    success = docker_service.stop_container(container_name, timeout=timeout)
                elif action == 'restart':
                    success = docker_service.restart_container(container_name, timeout=timeout)
                
                results[container_name] = {
                    'success': success,
                    'message': f'Container {action}ed successfully' if success else f'Failed to {action} container'
                }
            except Exception as e:
                results[container_name] = {
                    'success': False,
                    'error': str(e)
                }
        
        overall_success = all(result['success'] for result in results.values())
        
        return jsonify({
            'success': overall_success,
            'results': results,
            'action': action,
            'total': len(container_names),
            'successful': sum(1 for r in results.values() if r['success'])
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in bulk container action: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@containers_bp.route('/prune', methods=['POST'])
def prune_containers():
    """Remove stopped containers"""
    try:
        filters = request.json.get('filters', {}) if request.is_json else {}
        docker_service = get_docker_service()
        result = docker_service.prune_containers(filters=filters)
        
        return jsonify({
            'success': result['success'],
            'message': 'Container pruning completed' if result['success'] else 'Container pruning failed',
            'output': result.get('output', ''),
            'error': result.get('error', '')
        })
        
    except Exception as e:
        logger.error(f"Unexpected error pruning containers: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@containers_bp.route('/docker/info', methods=['GET'])
def get_docker_info():
    """Get Docker system information"""
    try:
        docker_service = get_docker_service()
        info = docker_service.get_docker_system_info()
        
        return jsonify({
            'success': True,
            'data': info
        })
        
    except Exception as e:
        logger.error(f"Unexpected error getting Docker info: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
