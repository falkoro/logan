"""API endpoints for container management."""
import logging
from flask import Blueprint, jsonify, request
from typing import Dict, Any, List

from ..services import DockerService
from ..models.container import ContainerModel

logger = logging.getLogger(__name__)

containers_bp = Blueprint('containers', __name__)


def init_containers_api(docker_service: DockerService):
    """Initialize the containers API with services."""
    containers_bp.docker_service = docker_service


@containers_bp.route('/api/containers', methods=['GET'])
def list_containers():
    """List all containers."""
    try:
        all_containers = request.args.get('all', 'true').lower() == 'true'
        containers = containers_bp.docker_service.list_containers(all_containers)
        
        return jsonify({
            'status': 'success',
            'data': [container.to_dict() for container in containers],
            'count': len(containers)
        })
        
    except Exception as e:
        logger.error(f"Error listing containers: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@containers_bp.route('/api/containers/managed', methods=['GET'])
def list_managed_containers():
    """List managed service containers only."""
    try:
        containers = containers_bp.docker_service.get_managed_services_status()
        
        return jsonify({
            'status': 'success',
            'data': [container.to_dict() for container in containers],
            'count': len(containers)
        })
        
    except Exception as e:
        logger.error(f"Error listing managed containers: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@containers_bp.route('/api/containers/<container_id_or_name>', methods=['GET'])
def get_container_details(container_id_or_name: str):
    """Get detailed information about a specific container."""
    try:
        container = containers_bp.docker_service.get_container_details(container_id_or_name)
        
        if container is None:
            return jsonify({
                'status': 'error',
                'message': f'Container {container_id_or_name} not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': container.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting container details: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@containers_bp.route('/api/containers/<container_id_or_name>/start', methods=['POST'])
def start_container(container_id_or_name: str):
    """Start a container."""
    try:
        success = containers_bp.docker_service.start_container(container_id_or_name)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Container {container_id_or_name} started successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to start container {container_id_or_name}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error starting container: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@containers_bp.route('/api/containers/<container_id_or_name>/stop', methods=['POST'])
def stop_container(container_id_or_name: str):
    """Stop a container."""
    try:
        timeout = request.json.get('timeout', 10) if request.is_json else 10
        success = containers_bp.docker_service.stop_container(container_id_or_name, timeout)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Container {container_id_or_name} stopped successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to stop container {container_id_or_name}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error stopping container: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@containers_bp.route('/api/containers/<container_id_or_name>/restart', methods=['POST'])
def restart_container(container_id_or_name: str):
    """Restart a container."""
    try:
        timeout = request.json.get('timeout', 10) if request.is_json else 10
        success = containers_bp.docker_service.restart_container(container_id_or_name, timeout)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Container {container_id_or_name} restarted successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to restart container {container_id_or_name}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error restarting container: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@containers_bp.route('/api/containers/<container_id_or_name>/logs', methods=['GET'])
def get_container_logs(container_id_or_name: str):
    """Get container logs."""
    try:
        tail = request.args.get('tail', 100, type=int)
        since = request.args.get('since')
        
        logs = containers_bp.docker_service.get_container_logs(
            container_id_or_name, tail=tail, since=since
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'container': container_id_or_name,
                'logs': logs,
                'lines': len(logs.splitlines()) if logs else 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting container logs: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@containers_bp.route('/api/containers/<container_id_or_name>/stats', methods=['GET'])
def get_container_stats(container_id_or_name: str):
    """Get container resource usage statistics."""
    try:
        stats = containers_bp.docker_service.get_container_stats(container_id_or_name)
        
        return jsonify({
            'status': 'success',
            'data': {
                'container': container_id_or_name,
                'stats': stats
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting container stats: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@containers_bp.route('/api/containers/bulk/action', methods=['POST'])
def bulk_container_action():
    """Perform bulk actions on multiple containers."""
    try:
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Request must be JSON'
            }), 400
        
        data = request.json
        action = data.get('action')
        container_names = data.get('containers', [])
        timeout = data.get('timeout', 10)
        
        if not action or not container_names:
            return jsonify({
                'status': 'error',
                'message': 'Action and containers list are required'
            }), 400
        
        valid_actions = ['start', 'stop', 'restart']
        if action not in valid_actions:
            return jsonify({
                'status': 'error',
                'message': f'Invalid action. Must be one of: {valid_actions}'
            }), 400
        
        results = {}
        for container_name in container_names:
            try:
                if action == 'start':
                    success = containers_bp.docker_service.start_container(container_name)
                elif action == 'stop':
                    success = containers_bp.docker_service.stop_container(container_name, timeout)
                elif action == 'restart':
                    success = containers_bp.docker_service.restart_container(container_name, timeout)
                
                results[container_name] = {
                    'success': success,
                    'message': f'Container {action}ed successfully' if success else f'Failed to {action} container'
                }
                
            except Exception as e:
                results[container_name] = {
                    'success': False,
                    'message': str(e)
                }
        
        # Count successes and failures
        successes = sum(1 for result in results.values() if result['success'])
        failures = len(results) - successes
        
        return jsonify({
            'status': 'success' if failures == 0 else 'partial',
            'message': f'Action {action} completed. {successes} successful, {failures} failed',
            'data': results,
            'summary': {
                'total': len(container_names),
                'successful': successes,
                'failed': failures
            }
        })
        
    except Exception as e:
        logger.error(f"Error performing bulk container action: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
