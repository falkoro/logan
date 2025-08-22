"""
System monitoring API endpoints
"""
import logging
from flask import Blueprint, request, jsonify, current_app
from app.services import MonitoringService, MonitoringServiceError

logger = logging.getLogger(__name__)

system_bp = Blueprint('system', __name__, url_prefix='/api/system')

def get_monitoring_service() -> MonitoringService:
    """Get Monitoring service instance from app context"""
    return current_app.monitoring_service

@system_bp.route('/info', methods=['GET'])
def get_system_info():
    """Get comprehensive system information"""
    try:
        monitoring_service = get_monitoring_service()
        system_info = monitoring_service.get_system_info()
        
        if system_info is None:
            return jsonify({
                'success': False,
                'error': 'Failed to retrieve system information'
            }), 500
        
        return jsonify({
            'success': True,
            'data': system_info.to_dict()
        })
        
    except MonitoringServiceError as e:
        logger.error(f"Monitoring service error getting system info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error getting system info: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@system_bp.route('/cpu', methods=['GET'])
def get_cpu_info():
    """Get CPU information and statistics"""
    try:
        monitoring_service = get_monitoring_service()
        cpu_info = monitoring_service.get_cpu_info()
        
        if cpu_info is None:
            return jsonify({
                'success': False,
                'error': 'Failed to retrieve CPU information'
            }), 500
        
        return jsonify({
            'success': True,
            'data': cpu_info
        })
        
    except MonitoringServiceError as e:
        logger.error(f"Monitoring service error getting CPU info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error getting CPU info: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@system_bp.route('/memory', methods=['GET'])
def get_memory_info():
    """Get memory information and statistics"""
    try:
        monitoring_service = get_monitoring_service()
        memory_info = monitoring_service.get_memory_info()
        
        if memory_info is None:
            return jsonify({
                'success': False,
                'error': 'Failed to retrieve memory information'
            }), 500
        
        return jsonify({
            'success': True,
            'data': memory_info
        })
        
    except MonitoringServiceError as e:
        logger.error(f"Monitoring service error getting memory info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error getting memory info: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@system_bp.route('/disk', methods=['GET'])
def get_disk_info():
    """Get disk information and statistics"""
    try:
        monitoring_service = get_monitoring_service()
        disk_info = monitoring_service.get_disk_info()
        
        if disk_info is None:
            return jsonify({
                'success': False,
                'error': 'Failed to retrieve disk information'
            }), 500
        
        return jsonify({
            'success': True,
            'data': disk_info
        })
        
    except MonitoringServiceError as e:
        logger.error(f"Monitoring service error getting disk info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error getting disk info: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@system_bp.route('/network', methods=['GET'])
def get_network_info():
    """Get network interface information and statistics"""
    try:
        monitoring_service = get_monitoring_service()
        network_info = monitoring_service.get_network_info()
        
        if network_info is None:
            return jsonify({
                'success': False,
                'error': 'Failed to retrieve network information'
            }), 500
        
        return jsonify({
            'success': True,
            'data': network_info
        })
        
    except MonitoringServiceError as e:
        logger.error(f"Monitoring service error getting network info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error getting network info: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@system_bp.route('/processes', methods=['GET'])
def get_process_info():
    """Get running process information"""
    try:
        monitoring_service = get_monitoring_service()
        process_info = monitoring_service.get_process_info()
        
        if process_info is None:
            return jsonify({
                'success': False,
                'error': 'Failed to retrieve process information'
            }), 500
        
        return jsonify({
            'success': True,
            'data': process_info
        })
        
    except MonitoringServiceError as e:
        logger.error(f"Monitoring service error getting process info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error getting process info: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@system_bp.route('/sensors', methods=['GET'])
def get_sensors_info():
    """Get temperature and sensor information"""
    try:
        monitoring_service = get_monitoring_service()
        sensors_info = monitoring_service.get_sensors_info()
        
        if sensors_info is None:
            return jsonify({
                'success': False,
                'error': 'Failed to retrieve sensors information'
            }), 500
        
        return jsonify({
            'success': True,
            'data': sensors_info
        })
        
    except MonitoringServiceError as e:
        logger.error(f"Monitoring service error getting sensors info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error getting sensors info: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@system_bp.route('/uptime', methods=['GET'])
def get_uptime_info():
    """Get system uptime information"""
    try:
        monitoring_service = get_monitoring_service()
        uptime_info = monitoring_service.get_uptime_info()
        
        if uptime_info is None:
            return jsonify({
                'success': False,
                'error': 'Failed to retrieve uptime information'
            }), 500
        
        return jsonify({
            'success': True,
            'data': uptime_info
        })
        
    except MonitoringServiceError as e:
        logger.error(f"Monitoring service error getting uptime info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error getting uptime info: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@system_bp.route('/load', methods=['GET'])
def get_system_load():
    """Get system load average information"""
    try:
        monitoring_service = get_monitoring_service()
        load_info = monitoring_service.get_system_load()
        
        if load_info is None:
            return jsonify({
                'success': False,
                'error': 'Failed to retrieve system load information'
            }), 500
        
        return jsonify({
            'success': True,
            'data': load_info
        })
        
    except MonitoringServiceError as e:
        logger.error(f"Monitoring service error getting system load: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error getting system load: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@system_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get system alerts"""
    try:
        monitoring_service = get_monitoring_service()
        alerts = monitoring_service.get_alert_info()
        
        if alerts is None:
            return jsonify({
                'success': False,
                'error': 'Failed to retrieve alert information'
            }), 500
        
        return jsonify({
            'success': True,
            'data': alerts
        })
        
    except MonitoringServiceError as e:
        logger.error(f"Monitoring service error getting alerts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error getting alerts: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@system_bp.route('/summary', methods=['GET'])
def get_system_summary():
    """Get summarized system metrics"""
    try:
        monitoring_service = get_monitoring_service()
        summary = monitoring_service.get_system_summary()
        
        return jsonify({
            'success': True,
            'data': summary
        })
        
    except MonitoringServiceError as e:
        logger.error(f"Monitoring service error getting system summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error getting system summary: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@system_bp.route('/historical/<plugin>', methods=['GET'])
def get_historical_data(plugin: str):
    """Get historical data for a specific plugin"""
    try:
        nb = int(request.args.get('entries', 10))
        monitoring_service = get_monitoring_service()
        historical_data = monitoring_service.get_historical_data(plugin, nb=nb)
        
        if historical_data is None:
            return jsonify({
                'success': False,
                'error': f'Failed to retrieve historical data for {plugin}'
            }), 500
        
        return jsonify({
            'success': True,
            'data': {
                'plugin': plugin,
                'entries': historical_data,
                'count': len(historical_data)
            }
        })
        
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Invalid entries parameter, must be integer'
        }), 400
    except MonitoringServiceError as e:
        logger.error(f"Monitoring service error getting historical data for {plugin}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error getting historical data for {plugin}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@system_bp.route('/plugins', methods=['GET'])
def get_plugins_list():
    """Get list of available Glances plugins"""
    try:
        monitoring_service = get_monitoring_service()
        plugins = monitoring_service.get_plugin_list()
        
        if plugins is None:
            return jsonify({
                'success': False,
                'error': 'Failed to retrieve plugins list'
            }), 500
        
        return jsonify({
            'success': True,
            'data': plugins
        })
        
    except MonitoringServiceError as e:
        logger.error(f"Monitoring service error getting plugins list: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error getting plugins list: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@system_bp.route('/health', methods=['GET'])
def check_monitoring_health():
    """Check monitoring service health"""
    try:
        monitoring_service = get_monitoring_service()
        is_healthy = monitoring_service.test_connection()
        
        return jsonify({
            'success': True,
            'data': {
                'healthy': is_healthy,
                'service': 'Glances API',
                'endpoint': f"{monitoring_service.base_url}/api/{monitoring_service.api_version}",
                'status': 'connected' if is_healthy else 'disconnected'
            }
        })
        
    except Exception as e:
        logger.error(f"Unexpected error checking monitoring health: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
