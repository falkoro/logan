"""
Glances API Proxy endpoint
Provides direct access to Glances API through SSH tunnel
"""
import logging
import json
import requests
from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any

logger = logging.getLogger(__name__)

glances_proxy_bp = Blueprint('glances_proxy', __name__, url_prefix='/api/glances')

def get_glances_config():
    """Get Glances configuration from app config"""
    return {
        'host': current_app.config.get('GLANCES_HOST', 'logan-GL502VS'),
        'port': current_app.config.get('GLANCES_PORT', 108),
        'api_version': current_app.config.get('GLANCES_API_VERSION', '3'),
        'timeout': current_app.config.get('GLANCES_TIMEOUT', 5)
    }

def make_glances_request(endpoint: str, max_retries: int = 3, **kwargs):
    """Make request to Glances API with retry logic"""
    config = get_glances_config()
    base_url = f"http://{config['host']}:{config['port']}/api/{config['api_version']}"
    url = f"{base_url}/{endpoint.lstrip('/')}"
    
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=config['timeout'], **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError as e:
            last_exception = Exception(f"Cannot connect to Glances API at {config['host']}:{config['port']} (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                import time
                time.sleep(1 * (attempt + 1))  # Exponential backoff
                continue
        except requests.exceptions.Timeout as e:
            last_exception = Exception(f"Glances API request timed out after {config['timeout']} seconds (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                continue
        except requests.exceptions.HTTPError as e:
            # Don't retry on HTTP errors like 404, 500, etc.
            raise Exception(f"Glances API HTTP error: {e}")
        except requests.exceptions.RequestException as e:
            last_exception = Exception(f"Glances API request failed: {e} (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                import time
                time.sleep(1 * (attempt + 1))
                continue
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response from Glances API: {e}")
    
    # If we get here, all retries failed
    raise last_exception or Exception(f"All {max_retries} attempts to connect to Glances API failed")

@glances_proxy_bp.route('/status', methods=['GET'])
def glances_status():
    """Get Glances server status"""
    try:
        data = make_glances_request('status')
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        logger.error(f"Error getting Glances status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@glances_proxy_bp.route('/system', methods=['GET'])
def glances_system():
    """Get system information from Glances"""
    try:
        data = make_glances_request('system')
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        logger.error(f"Error getting Glances system info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@glances_proxy_bp.route('/cpu', methods=['GET'])
def glances_cpu():
    """Get CPU information from Glances"""
    try:
        data = make_glances_request('cpu')
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        logger.error(f"Error getting Glances CPU info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@glances_proxy_bp.route('/memory', methods=['GET'])
def glances_memory():
    """Get memory information from Glances"""
    try:
        data = make_glances_request('mem')
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        logger.error(f"Error getting Glances memory info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@glances_proxy_bp.route('/load', methods=['GET'])
def glances_load():
    """Get system load from Glances"""
    try:
        data = make_glances_request('load')
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        logger.error(f"Error getting Glances load info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@glances_proxy_bp.route('/network', methods=['GET'])
def glances_network():
    """Get network information from Glances"""
    try:
        data = make_glances_request('network')
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        logger.error(f"Error getting Glances network info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@glances_proxy_bp.route('/disk', methods=['GET'])
def glances_disk():
    """Get disk information from Glances"""
    try:
        data = make_glances_request('fs')
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        logger.error(f"Error getting Glances disk info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@glances_proxy_bp.route('/processes', methods=['GET'])
def glances_processes():
    """Get process list from Glances"""
    try:
        data = make_glances_request('processlist')
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        logger.error(f"Error getting Glances processes: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@glances_proxy_bp.route('/docker', methods=['GET'])
def glances_docker():
    """Get Docker container info from Glances"""
    try:
        data = make_glances_request('containers')
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        logger.error(f"Error getting Glances Docker info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@glances_proxy_bp.route('/containers', methods=['GET'])
def glances_containers():
    """Get container info from Glances"""
    try:
        data = make_glances_request('containers')
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        logger.error(f"Error getting Glances container info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@glances_proxy_bp.route('/all', methods=['GET'])
def glances_all():
    """Get all available data from Glances"""
    try:
        data = make_glances_request('all')
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        logger.error(f"Error getting all Glances data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@glances_proxy_bp.route('/config', methods=['GET'])
def glances_config():
    """Get Glances configuration"""
    try:
        config = get_glances_config()
        return jsonify({
            'success': True,
            'data': {
                'host': config['host'],
                'port': config['port'],
                'api_version': config['api_version'],
                'base_url': f"http://{config['host']}:{config['port']}/api/{config['api_version']}"
            }
        })
    except Exception as e:
        logger.error(f"Error getting Glances config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@glances_proxy_bp.route('/debug', methods=['GET'])
def glances_debug():
    """Debug Glances connectivity"""
    try:
        import requests
        config = get_glances_config()
        
        results = {}
        
        # Try different common configurations
        test_configs = [
            {'port': 61208, 'api_version': '3', 'endpoint': 'status'},
            {'port': 61208, 'api_version': '3', 'endpoint': ''},
            {'port': 61208, 'api_version': '3', 'endpoint': 'system'},
            {'port': 61208, 'api_version': '3', 'endpoint': 'cpu'},
            {'port': 61208, 'api_version': '3', 'endpoint': 'mem'},
            {'port': 61208, 'api_version': '3', 'endpoint': 'help'},
            {'port': 61208, 'api_version': '2', 'endpoint': 'status'},
            {'port': 61208, 'api_version': '1', 'endpoint': 'status'},
            {'port': 108, 'api_version': '3', 'endpoint': 'status'},
        ]
        
        for i, test_config in enumerate(test_configs):
            test_url = f"http://{config['host']}:{test_config['port']}/api/{test_config['api_version']}/{test_config['endpoint']}"
            try:
                response = requests.get(test_url, timeout=3)
                results[f'test_{i+1}'] = {
                    'url': test_url,
                    'status_code': response.status_code,
                    'success': response.status_code == 200,
                    'response_size': len(response.content)
                }
            except requests.exceptions.ConnectionError:
                results[f'test_{i+1}'] = {
                    'url': test_url,
                    'error': 'Connection refused',
                    'success': False
                }
            except Exception as e:
                results[f'test_{i+1}'] = {
                    'url': test_url,
                    'error': str(e),
                    'success': False
                }
        
        return jsonify({
            'success': True,
            'current_config': config,
            'tests': results
        })
        
    except Exception as e:
        logger.error(f"Error debugging Glances connectivity: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
