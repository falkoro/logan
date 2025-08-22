"""
Flask Application Factory and Configuration
"""
import logging
import os
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from app.config import config
from app.api import containers_bp, system_bp, health_bp
from app.api.docker_proxy import docker_proxy_bp
from app.api.glances_proxy import glances_proxy_bp
from app.services import SSHService, DockerService, MonitoringService

def create_app(config_name: str = None) -> Flask:
    """
    Application factory pattern for creating Flask app
    
    Args:
        config_name: Configuration environment name
        
    Returns:
        Configured Flask application
    """
    # Determine configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    CORS(app)
    # Temporarily disable SocketIO due to Windows permission issues
    # socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Configure logging
    setup_logging(app)
    
    # Initialize services
    setup_services(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register WebSocket events (disabled for now)
    # register_websocket_events(socketio, app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register CLI commands
    register_commands(app)
    
    # Store SocketIO instance for later use (create a dummy one)
    class DummySocketIO:
        def run(self, *args, **kwargs):
            raise Exception("SocketIO disabled")
    
    app.socketio = DummySocketIO()
    
    return app

def setup_logging(app: Flask):
    """Configure application logging"""
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure file logging if specified
    log_file = app.config.get('LOG_FILE')
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_format))
        
        app.logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('socketio').setLevel(logging.WARNING)
    logging.getLogger('engineio').setLevel(logging.WARNING)

def setup_services(app: Flask):
    """Initialize application services"""
    try:
        # Get the config class for services
        config_name = os.environ.get('FLASK_ENV', 'development')
        config_class = config[config_name]
        service_config = config_class()
        
        # Initialize SSH service
        ssh_service = SSHService(service_config)
        app.ssh_service = ssh_service
        
        # Initialize Docker service
        docker_service = DockerService(ssh_service)
        app.docker_service = docker_service
        
        # Initialize Monitoring service
        monitoring_service = MonitoringService(service_config)
        app.monitoring_service = monitoring_service

        app.logger.info("Services initialized successfully")

    except Exception as e:
        app.logger.error(f"Failed to initialize services: {e}")
        # Don't raise exception to allow app to start in degraded mode

def register_blueprints(app: Flask):
    """Register application blueprints"""
    app.register_blueprint(containers_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(docker_proxy_bp)
    app.register_blueprint(glances_proxy_bp)
    
    # Register main routes
    @app.route('/')
    def index():
        """Main dashboard page"""
        from flask import render_template
        return render_template('index.html')
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        from flask import jsonify
        try:
            # Test services
            ssh_healthy = app.ssh_service.test_connection()
            docker_healthy = app.ssh_service.test_docker_access()
            monitoring_healthy = app.monitoring_service.test_connection()
            
            return jsonify({
                'status': 'healthy',
                'services': {
                    'ssh': {'healthy': ssh_healthy, 'host': app.config['REMOTE_HOST']},
                    'docker': {'healthy': docker_healthy, 'remote': True},
                    'monitoring': {
                        'healthy': monitoring_healthy, 
                        'endpoint': f"{app.config['GLANCES_HOST']}:{app.config['GLANCES_PORT']}"
                    }
                }
            })
        except Exception as e:
            app.logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 500
    
    @app.route('/api/services')
    def get_services():
        """Get target services configuration"""
        from flask import jsonify
        services = app.config.get('TARGET_SERVICES', {})
        
        # Group services by category
        grouped_services = {}
        for service_id, service_config in services.items():
            category = service_config.get('category', 'other')
            if category not in grouped_services:
                grouped_services[category] = []
            
            grouped_services[category].append({
                'id': service_id,
                'name': service_config.get('name', service_id),
                'port': service_config.get('port'),
                'vpn_required': service_config.get('vpn_required', False),
                'url': f"http://{app.config['REMOTE_HOST']}:{service_config.get('port')}"
            })
        
        return jsonify({
            'success': True,
            'data': grouped_services
        })

def register_websocket_events(socketio: SocketIO, app: Flask):
    """Register WebSocket events for real-time updates"""
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        app.logger.info(f"Client connected")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        app.logger.info(f"Client disconnected")
    
    @socketio.on('request_container_update')
    def handle_container_update_request():
        """Handle request for container updates"""
        try:
            containers = app.docker_service.list_containers()
            container_data = [container.to_dict() for container in containers]
            
            socketio.emit('container_update', {
                'containers': container_data,
                'timestamp': containers[0].stats.timestamp.isoformat() if containers and containers[0].stats else None
            })
        except Exception as e:
            app.logger.error(f"Error sending container update: {e}")
            socketio.emit('error', {'message': 'Failed to get container data'})
    
    @socketio.on('request_system_update')
    def handle_system_update_request():
        """Handle request for system updates"""
        try:
            system_info = app.monitoring_service.get_system_info()
            if system_info:
                socketio.emit('system_update', system_info.to_dict())
            else:
                socketio.emit('error', {'message': 'Failed to get system data'})
        except Exception as e:
            app.logger.error(f"Error sending system update: {e}")
            socketio.emit('error', {'message': 'Failed to get system data'})

def register_error_handlers(app: Flask):
    """Register application error handlers"""
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        from flask import jsonify, request
        if request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'error': 'Endpoint not found'
            }), 404
        else:
            from flask import render_template
            return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        from flask import jsonify, request
        app.logger.error(f"Internal server error: {error}")
        
        if request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
        else:
            from flask import render_template
            return render_template('500.html'), 500

def register_commands(app: Flask):
    """Register CLI commands"""
    @app.cli.command()
    def test_connections():
        """Test all service connections"""
        print("Testing service connections...")
        
        # Test SSH connection
        print(f"SSH connection to {app.config['REMOTE_HOST']}...", end=' ')
        if app.ssh_service.test_connection():
            print("✓ Connected")
        else:
            print("✗ Failed")
        
        # Test Docker access
        print(f"Docker access via SSH...", end=' ')
        if app.ssh_service.test_docker_access():
            print("✓ Connected")
        else:
            print("✗ Failed")
        
        # Test Glances API
        print(f"Glances API at {app.config['GLANCES_HOST']}:{app.config['GLANCES_PORT']}...", end=' ')
        if app.monitoring_service.test_connection():
            print("✓ Connected")
        else:
            print("✗ Failed")
    
    @app.cli.command()
    def list_containers():
        """List all containers"""
        try:
            containers = app.docker_service.list_containers()
            print(f"\nFound {len(containers)} containers:")
            print(f"{'Name':<20} {'Status':<10} {'Image':<30} {'Ports'}")
            print("-" * 80)
            
            for container in containers:
                ports = ', '.join([f"{p.host_port}:{p.container_port}" for p in container.ports])
                print(f"{container.name:<20} {container.status.value:<10} {container.image:<30} {ports}")
                
        except Exception as e:
            print(f"Error listing containers: {e}")
    
    @app.cli.command()
    def show_system_info():
        """Show system information"""
        try:
            system_info = app.monitoring_service.get_system_info()
            if system_info:
                print(f"\nSystem Information:")
                print(f"Hostname: {system_info.hostname}")
                print(f"Platform: {system_info.platform}")
                print(f"Uptime: {system_info.uptime_formatted}")
                print(f"CPU Usage: {system_info.cpu.percent:.1f}%")
                print(f"Memory Usage: {system_info.memory.percent:.1f}% ({system_info.memory.used_gb:.1f}GB / {system_info.memory.total_gb:.1f}GB)")
                print(f"Disk Usage: {system_info.disk_usage_percent:.1f}% ({system_info.used_disk_space_gb:.1f}GB / {system_info.total_disk_space_gb:.1f}GB)")
            else:
                print("Failed to get system information")
        except Exception as e:
            print(f"Error getting system info: {e}")
