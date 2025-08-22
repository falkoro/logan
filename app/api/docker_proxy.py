"""
Docker API Proxy endpoint
Provides direct access to Docker API through SSH tunnel
"""
import logging
import json
from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any

logger = logging.getLogger(__name__)

docker_proxy_bp = Blueprint('docker_proxy', __name__, url_prefix='/api/docker')

def get_docker_service():
    """Get Docker service instance from app context"""
    return current_app.docker_service

@docker_proxy_bp.route('/version', methods=['GET'])
def docker_version():
    """Get Docker version information"""
    try:
        docker_service = get_docker_service()
        exit_code, stdout, stderr = docker_service.ssh.execute_docker_command('version --format json')
        
        if exit_code != 0:
            logger.error(f"Docker version command failed: {stderr}")
            return jsonify({
                'success': False,
                'error': f'Docker version command failed: {stderr}'
            }), 500
        
        version_info = json.loads(stdout)
        return jsonify({
            'success': True,
            'data': version_info
        })
        
    except Exception as e:
        logger.error(f"Error getting Docker version: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@docker_proxy_bp.route('/info', methods=['GET'])
def docker_info():
    """Get Docker system information"""
    try:
        docker_service = get_docker_service()
        exit_code, stdout, stderr = docker_service.ssh.execute_docker_command('info --format json')
        
        if exit_code != 0:
            logger.error(f"Docker info command failed: {stderr}")
            return jsonify({
                'success': False,
                'error': f'Docker info command failed: {stderr}'
            }), 500
        
        info_data = json.loads(stdout)
        return jsonify({
            'success': True,
            'data': info_data
        })
        
    except Exception as e:
        logger.error(f"Error getting Docker info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@docker_proxy_bp.route('/stats', methods=['GET'])
def docker_stats():
    """Get Docker container statistics"""
    try:
        docker_service = get_docker_service()
        container_names = request.args.getlist('names')  # Get specific containers
        
        if container_names:
            # Get stats for specific containers
            cmd = f"stats --no-stream --format json {' '.join(container_names)}"
        else:
            # Get stats for all containers
            cmd = "stats --no-stream --format json"
        
        exit_code, stdout, stderr = docker_service.ssh.execute_docker_command(cmd, timeout=30)
        
        if exit_code != 0:
            logger.error(f"Docker stats command failed: {stderr}")
            return jsonify({
                'success': False,
                'error': f'Docker stats command failed: {stderr}'
            }), 500
        
        stats_data = []
        if stdout.strip():
            for line in stdout.strip().split('\n'):
                try:
                    stats_data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        return jsonify({
            'success': True,
            'data': stats_data
        })
        
    except Exception as e:
        logger.error(f"Error getting Docker stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@docker_proxy_bp.route('/ps', methods=['GET'])
def docker_ps():
    """Get Docker container list"""
    try:
        docker_service = get_docker_service()
        
        # Parse query parameters
        all_containers = request.args.get('all', 'false').lower() == 'true'
        format_option = request.args.get('format', 'json')
        
        cmd_args = []
        if all_containers:
            cmd_args.append('-a')
        cmd_args.append(f'--format {format_option}')
        
        cmd = f"ps {' '.join(cmd_args)}"
        
        exit_code, stdout, stderr = docker_service.ssh.execute_docker_command(cmd)
        
        if exit_code != 0:
            logger.error(f"Docker ps command failed: {stderr}")
            return jsonify({
                'success': False,
                'error': f'Docker ps command failed: {stderr}'
            }), 500
        
        if format_option == 'json':
            containers_data = []
            if stdout.strip():
                for line in stdout.strip().split('\n'):
                    try:
                        containers_data.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            
            return jsonify({
                'success': True,
                'data': containers_data
            })
        else:
            return jsonify({
                'success': True,
                'data': stdout
            })
        
    except Exception as e:
        logger.error(f"Error getting Docker ps: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@docker_proxy_bp.route('/exec/<container_name>', methods=['POST'])
def docker_exec(container_name: str):
    """Execute command in Docker container"""
    try:
        docker_service = get_docker_service()
        data = request.get_json()
        
        if not data or 'command' not in data:
            return jsonify({
                'success': False,
                'error': 'Command is required'
            }), 400
        
        command = data['command']
        interactive = data.get('interactive', False)
        tty = data.get('tty', False)
        
        # Build exec command
        exec_options = []
        if interactive:
            exec_options.append('-i')
        if tty:
            exec_options.append('-t')
        
        exec_cmd = f"exec {' '.join(exec_options)} {container_name} {command}"
        
        exit_code, stdout, stderr = docker_service.ssh.execute_docker_command(exec_cmd, timeout=60)
        
        return jsonify({
            'success': True,
            'data': {
                'exit_code': exit_code,
                'stdout': stdout,
                'stderr': stderr
            }
        })
        
    except Exception as e:
        logger.error(f"Error executing Docker command: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@docker_proxy_bp.route('/logs/<container_name>', methods=['GET'])
def docker_logs(container_name: str):
    """Get Docker container logs"""
    try:
        docker_service = get_docker_service()
        
        # Parse query parameters
        lines = request.args.get('lines', '100')
        follow = request.args.get('follow', 'false').lower() == 'true'
        timestamps = request.args.get('timestamps', 'true').lower() == 'true'
        since = request.args.get('since')
        
        cmd_options = []
        if not follow:  # Don't follow for API requests unless explicitly requested
            cmd_options.append('--tail')
            cmd_options.append(lines)
        if timestamps:
            cmd_options.append('--timestamps')
        if since:
            cmd_options.append(f'--since {since}')
        
        cmd = f"logs {' '.join(cmd_options)} {container_name}"
        
        exit_code, stdout, stderr = docker_service.ssh.execute_docker_command(cmd, timeout=30)
        
        if exit_code != 0:
            logger.error(f"Docker logs command failed: {stderr}")
            return jsonify({
                'success': False,
                'error': f'Docker logs command failed: {stderr}'
            }), 500
        
        return jsonify({
            'success': True,
            'data': {
                'logs': stdout,
                'container': container_name
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting Docker logs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
