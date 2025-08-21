"""Application configuration module."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class."""
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-me'
    FLASK_ENV = os.environ.get('FLASK_ENV') or 'development'
    
    # SSH Configuration
    SSH_HOST = os.environ.get('SSH_HOST') or 'logan-GL502VS'
    SSH_USERNAME = os.environ.get('SSH_USERNAME') or 'logan'
    SSH_PORT = int(os.environ.get('SSH_PORT', 22))
    SSH_KEY_PATH = os.environ.get('SSH_KEY_PATH')
    SSH_TIMEOUT = int(os.environ.get('SSH_TIMEOUT', 30))
    
    # Docker Configuration
    DOCKER_SOCKET = os.environ.get('DOCKER_SOCKET') or 'unix:///var/run/docker.sock'
    
    # Application Configuration
    HOST = os.environ.get('HOST') or '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5000))
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'dashboard.log'
    
    # Service Configuration
    SERVICES_CONFIG_FILE = os.environ.get('SERVICES_CONFIG_FILE') or 'services.json'
    
    # Monitoring Configuration
    HEALTH_CHECK_INTERVAL = int(os.environ.get('HEALTH_CHECK_INTERVAL', 30))
    METRICS_RETENTION_DAYS = int(os.environ.get('METRICS_RETENTION_DAYS', 7))
    
    # Service definitions - the specific services we manage
    MANAGED_SERVICES = {
        'sabnzbd': {
            'name': 'SABnzbd',
            'port': 101,
            'category': 'media',
            'description': 'Usenet downloader',
            'vpn_required': True,
            'container_name': 'sabnzbd'
        },
        'qbittorrent': {
            'name': 'qBittorrent',
            'port': 102,
            'category': 'media',
            'description': 'Torrent client',
            'vpn_required': True,
            'container_name': 'qbittorrent'
        },
        'sonarr': {
            'name': 'Sonarr',
            'port': 103,
            'category': 'media',
            'description': 'TV series management',
            'vpn_required': True,
            'container_name': 'sonarr'
        },
        'radarr': {
            'name': 'Radarr',
            'port': 105,
            'category': 'media',
            'description': 'Movie management',
            'vpn_required': True,
            'container_name': 'radarr'
        },
        'jackett': {
            'name': 'Jackett',
            'port': 106,
            'category': 'media',
            'description': 'Indexer proxy',
            'vpn_required': True,
            'container_name': 'jackett'
        },
        'plex': {
            'name': 'Plex',
            'port': 32400,
            'category': 'core',
            'description': 'Media server',
            'vpn_required': False,
            'container_name': 'plex'
        },
        'homarr': {
            'name': 'Homarr',
            'port': 107,
            'category': 'core',
            'description': 'Backup dashboard',
            'vpn_required': False,
            'container_name': 'homarr'
        },
        'glances': {
            'name': 'Glances',
            'port': 108,
            'category': 'monitoring',
            'description': 'System monitoring',
            'vpn_required': False,
            'container_name': 'glances'
        },
        'uptime-kuma': {
            'name': 'Uptime Kuma',
            'port': 109,
            'category': 'monitoring',
            'description': 'Service monitoring',
            'vpn_required': False,
            'container_name': 'uptime-kuma'
        },
        'smokeping': {
            'name': 'Smokeping',
            'port': 110,
            'category': 'monitoring',
            'description': 'Network monitoring',
            'vpn_required': False,
            'container_name': 'smokeping'
        },
        'icarus': {
            'name': 'Icarus',
            'port': 2777,
            'category': 'gaming',
            'description': 'Dedicated game server',
            'vpn_required': False,
            'container_name': 'icarus-server'
        }
    }


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    SSH_HOST = 'localhost'  # Use localhost for testing
    

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
