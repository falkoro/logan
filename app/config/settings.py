# Application Configuration
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1']
    
    # Remote SSH Configuration
    REMOTE_HOST = os.environ.get('REMOTE_HOST', 'localhost')
    REMOTE_USER = os.environ.get('REMOTE_USER', os.environ.get('USER', 'user'))
    SSH_KEY_PATH = os.path.expanduser(os.environ.get('SSH_KEY_PATH', '~/.ssh/id_rsa'))
    SSH_TIMEOUT = int(os.environ.get('SSH_TIMEOUT', 10))
    
    # Docker Configuration
    DOCKER_HOST = os.environ.get('DOCKER_HOST', 'unix:///var/run/docker.sock')
    
    # Glances API Configuration
    GLANCES_HOST = os.environ.get('GLANCES_HOST', 'localhost')
    GLANCES_PORT = int(os.environ.get('GLANCES_PORT', 61208))
    GLANCES_API_VERSION = os.environ.get('GLANCES_API_VERSION', '4')
    GLANCES_TIMEOUT = int(os.environ.get('GLANCES_TIMEOUT', 5))
    
    # Application Settings
    UPDATE_INTERVAL = int(os.environ.get('UPDATE_INTERVAL', 5))
    SERVICES_CONFIG_PATH = os.environ.get('SERVICES_CONFIG_PATH', './config/services.json')
    
    # Security Settings
    BASIC_AUTH_USERNAME = os.environ.get('BASIC_AUTH_USERNAME', 'admin')
    BASIC_AUTH_PASSWORD = os.environ.get('BASIC_AUTH_PASSWORD', 'changeme')
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'dashboard.log')
    
    # Target Services Configuration
    TARGET_SERVICES = {
        'sabnzbd': {'port': 101, 'name': 'SABnzbd', 'category': 'media', 'vpn_required': True},
        'qbittorrent': {'port': 102, 'name': 'qBittorrent', 'category': 'media', 'vpn_required': True},
        'sonarr': {'port': 103, 'name': 'Sonarr', 'category': 'media', 'vpn_required': True},
        'radarr': {'port': 105, 'name': 'Radarr', 'category': 'media', 'vpn_required': True},
        'jackett': {'port': 106, 'name': 'Jackett', 'category': 'media', 'vpn_required': True},
        'plex': {'port': 32400, 'name': 'Plex', 'category': 'core', 'vpn_required': False},
        'dashboard': {'port': 100, 'name': 'LoganGemma Dashboard', 'category': 'core', 'vpn_required': False},
        'homarr': {'port': 107, 'name': 'Homarr', 'category': 'core', 'vpn_required': False},
        'glances': {'port': 108, 'name': 'Glances', 'category': 'monitoring', 'vpn_required': False},
        'uptime-kuma': {'port': 109, 'name': 'Uptime Kuma', 'category': 'monitoring', 'vpn_required': False},
        'smokeping': {'port': 110, 'name': 'Smokeping', 'category': 'monitoring', 'vpn_required': False},
        'icarus': {'port': 2777, 'name': 'Icarus Game Server', 'category': 'gaming', 'vpn_required': False}
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    # Use local mock services for testing
    REMOTE_HOST = 'localhost'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
