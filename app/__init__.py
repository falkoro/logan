"""Flask application factory."""
import logging
import os
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

from .config.settings import config
from .services import SSHService, DockerService, MonitoringService
from .api import containers_bp, system_bp, init_containers_api, init_system_api


def create_app(config_name=None):
    """Create and configure Flask application.
    
    Args:
        config_name: Configuration name to use (development, testing, production)
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, app.config['LOG_LEVEL']),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Docker Dashboard in {config_name} mode")
    
    # Enable CORS
    CORS(app)
    
    # Initialize services
    ssh_service = SSHService(
        host=app.config['SSH_HOST'],
        username=app.config['SSH_USERNAME'],
        port=app.config['SSH_PORT'],
        key_path=app.config['SSH_KEY_PATH'],
        timeout=app.config['SSH_TIMEOUT']
    )
    
    docker_service = DockerService(ssh_service, app.config['MANAGED_SERVICES'])
    monitoring_service = MonitoringService(ssh_service, app.config['MANAGED_SERVICES'])
    
    # Initialize API blueprints
    init_containers_api(docker_service)
    init_system_api(monitoring_service)
    
    # Register blueprints
    app.register_blueprint(containers_bp)
    app.register_blueprint(system_bp)
    
    # Store services in app context for access in routes
    app.ssh_service = ssh_service
    app.docker_service = docker_service
    app.monitoring_service = monitoring_service
    
    # Main dashboard route
    @app.route('/')
    def dashboard():
        """Main dashboard page."""
        try:
            return render_template('dashboard.html', 
                                 services=app.config['MANAGED_SERVICES'],
                                 ssh_host=app.config['SSH_HOST'])
        except Exception as e:
            logger.error(f"Error rendering dashboard: {e}")
            return f"Error loading dashboard: {str(e)}", 500
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        """Health check endpoint."""
        try:
            # Test SSH connection
            ssh_status = ssh_service.is_connected() or ssh_service.connect()
            
            # Test Docker access if SSH is working
            docker_status = False
            if ssh_status:
                docker_status = ssh_service.test_docker_access()
            
            return jsonify({
                'status': 'healthy' if ssh_status and docker_status else 'unhealthy',
                'checks': {
                    'ssh_connection': ssh_status,
                    'docker_access': docker_status
                },
                'version': '1.0.0',
                'host': app.config['SSH_HOST']
            })
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 500
    
    # Service info endpoint
    @app.route('/api/services')
    def get_services():
        """Get list of managed services."""
        return jsonify({
            'status': 'success',
            'data': app.config['MANAGED_SERVICES']
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """404 error handler."""
        if request.path.startswith('/api/'):
            return jsonify({
                'status': 'error',
                'message': 'API endpoint not found'
            }), 404
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """500 error handler."""
        logger.error(f"Internal server error: {error}")
        if request.path.startswith('/api/'):
            return jsonify({
                'status': 'error',
                'message': 'Internal server error'
            }), 500
        return render_template('500.html'), 500
    
    # Cleanup function
    @app.teardown_appcontext
    def cleanup(error):
        """Clean up resources on app context teardown."""
        pass
    
    return app


def create_test_app():
    """Create app for testing with mocked services."""
    return create_app('testing')
