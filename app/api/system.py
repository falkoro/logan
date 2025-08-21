"""API endpoints for system monitoring."""
import logging
from flask import Blueprint, jsonify, request

from ..services import MonitoringService

logger = logging.getLogger(__name__)

system_bp = Blueprint('system', __name__)


def init_system_api(monitoring_service: MonitoringService):
    """Initialize the system API with services."""
    system_bp.monitoring_service = monitoring_service


@system_bp.route('/api/system/metrics', methods=['GET'])
def get_system_metrics():
    """Get current system metrics."""
    try:
        use_cache = request.args.get('cache', 'true').lower() == 'true'
        metrics = system_bp.monitoring_service.get_system_metrics(use_cache)
        
        if metrics is None:
            return jsonify({
                'status': 'error',
                'message': 'Failed to retrieve system metrics'
            }), 500
        
        return jsonify({
            'status': 'success',
            'data': metrics.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@system_bp.route('/api/system/metrics/history', methods=['GET'])
def get_historical_metrics():
    """Get historical system metrics."""
    try:
        hours = request.args.get('hours', 24, type=int)
        if hours < 1 or hours > 168:  # Max 1 week
            hours = 24
        
        metrics = system_bp.monitoring_service.get_historical_metrics(hours)
        
        return jsonify({
            'status': 'success',
            'data': [m.to_dict() for m in metrics],
            'count': len(metrics),
            'hours': hours
        })
        
    except Exception as e:
        logger.error(f"Error getting historical metrics: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@system_bp.route('/api/system/health', methods=['GET'])
def get_service_health():
    """Get health status of all managed services."""
    try:
        use_cache = request.args.get('cache', 'true').lower() == 'true'
        health_status = system_bp.monitoring_service.get_service_health_status(use_cache)
        
        return jsonify({
            'status': 'success',
            'data': [health.to_dict() for health in health_status],
            'count': len(health_status)
        })
        
    except Exception as e:
        logger.error(f"Error getting service health: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@system_bp.route('/api/system/info', methods=['GET'])
def get_system_info():
    """Get general system information."""
    try:
        system_info = system_bp.monitoring_service.get_system_info()
        
        if system_info is None:
            return jsonify({
                'status': 'error',
                'message': 'Failed to retrieve system information'
            }), 500
        
        return jsonify({
            'status': 'success',
            'data': system_info.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@system_bp.route('/api/system/network', methods=['GET'])
def get_network_info():
    """Get network interface information."""
    try:
        network_info = system_bp.monitoring_service.get_network_info()
        
        return jsonify({
            'status': 'success',
            'data': [net.to_dict() for net in network_info],
            'count': len(network_info)
        })
        
    except Exception as e:
        logger.error(f"Error getting network info: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@system_bp.route('/api/system/status', methods=['GET'])
def get_system_status():
    """Get overall system status summary."""
    try:
        # Get current metrics
        metrics = system_bp.monitoring_service.get_system_metrics(use_cache=True)
        
        # Get service health
        health_status = system_bp.monitoring_service.get_service_health_status(use_cache=True)
        
        # Calculate overall health
        total_services = len(health_status)
        healthy_services = sum(1 for h in health_status if h.is_healthy)
        
        # Determine overall status
        if total_services == 0:
            overall_status = 'unknown'
        elif healthy_services == total_services:
            overall_status = 'healthy'
        elif healthy_services >= total_services * 0.8:  # 80% threshold
            overall_status = 'warning'
        else:
            overall_status = 'critical'
        
        # System resource status
        resource_status = 'healthy'
        if metrics:
            if metrics.cpu_percent > 90 or metrics.memory_percent > 90 or metrics.disk_percent > 90:
                resource_status = 'critical'
            elif metrics.cpu_percent > 75 or metrics.memory_percent > 75 or metrics.disk_percent > 80:
                resource_status = 'warning'
        
        return jsonify({
            'status': 'success',
            'data': {
                'overall_status': overall_status,
                'resource_status': resource_status,
                'services': {
                    'total': total_services,
                    'healthy': healthy_services,
                    'unhealthy': total_services - healthy_services
                },
                'metrics': metrics.to_dict() if metrics else None,
                'last_updated': metrics.timestamp.isoformat() if metrics else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@system_bp.route('/api/system/cache/clear', methods=['POST'])
def clear_cache():
    """Clear monitoring cache."""
    try:
        system_bp.monitoring_service.clear_cache()
        
        return jsonify({
            'status': 'success',
            'message': 'Cache cleared successfully'
        })
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
