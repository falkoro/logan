# Docker Dashboard Project Prompt

## Project Overview
Create a modular, testable Python Flask web application that serves as a comprehensive dashboard for managing Docker containers across remote systems via SSH. This dashboard will replace the current Heimdall setup and provide advanced monitoring, management, and configuration capabilities.

## Core Requirements

### 1. Architecture & Design
- **Modular Structure**: Clean separation of concerns with distinct modules for different functionalities
- **Testable**: Comprehensive unit and integration tests using pytest
- **Local Development**: Support for local testing with Python virtual environments
- **Remote Management**: SSH-based container management for remote Docker hosts
- **RESTful API**: Clean API design for all operations

### 2. Core Functionality
- **Container Management**: Start, stop, restart, view logs for Docker containers
- **System Monitoring**: CPU, memory, disk usage, network statistics
- **Service Health Checks**: Monitor service availability and response times
- **Configuration Management**: Manage container configurations and environment variables
- **Log Aggregation**: Centralized log viewing and search capabilities

### 3. Target Services to Manage
The dashboard must manage these specific services currently running on `logan@logan-GL502VS`:

#### Media Services (VPN-enabled)
- **SABnzbd** (Port 101) - Usenet downloader
- **qBittorrent** (Port 102) - Torrent client  
- **Sonarr** (Port 103) - TV series management
- **Radarr** (Port 105) - Movie management
- **Jackett** (Port 106) - Indexer proxy

#### Core Services
- **Plex** (Port 32400) - Media server
- **Main Dashboard** (Port 100) - This application
- **Homarr** (Port 107) - Backup dashboard

#### Monitoring Services
- **Glances** (Port 108) - System monitoring
- **Uptime Kuma** (Port 109) - Service monitoring
- **Smokeping** (Port 110) - Network monitoring

#### Game Server
- **Icarus** (Port 2777/27015) - Dedicated game server

### 4. Technical Stack
- **Backend**: Python 3.9+ with Flask
- **Frontend**: Modern HTML5, CSS3, JavaScript (no heavy frameworks)
- **Testing**: pytest, pytest-flask, pytest-mock, pytest-cov
- **Deployment**: Docker container with docker-compose integration
- **Remote Access**: SSH with paramiko/fabric for remote operations
- **Monitoring**: Integration with existing monitoring tools

### 5. Key Features

#### Dashboard Interface
- **Overview Page**: System status, running containers, resource usage
- **Container Grid**: Visual cards showing container status, ports, health
- **Service Links**: Direct links to all managed services
- **Real-time Updates**: WebSocket or polling for live status updates

#### Management Features
- **One-click Actions**: Start/stop/restart containers
- **Bulk Operations**: Manage multiple containers simultaneously
- **Configuration Editor**: Edit container environment variables and settings
- **Log Viewer**: Real-time and historical log viewing with search
- **Health Monitoring**: Visual indicators for service health

#### Advanced Features
- **VPN Status**: Monitor VPN container connectivity
- **Port Conflict Detection**: Identify and resolve port conflicts
- **Backup Management**: Schedule and manage configuration backups
- **Alert System**: Notifications for service failures or resource issues

### 6. File Structure
```
dashboard/
├── .github/
│   └── copilot-instructions.md
├── app/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── container.py
│   │   └── system.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── docker_service.py
│   │   ├── ssh_service.py
│   │   └── monitoring_service.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── containers.py
│   │   └── system.py
│   └── static/
│       ├── css/
│       ├── js/
│       └── img/
├── tests/
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── requirements.txt
├── requirements-dev.txt
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── .gitignore
├── README.md
└── run.py
```

### 7. Environment Configuration
- **SSH Connection**: `logan@logan-GL502VS` with key-based authentication
- **Docker Socket**: Remote Docker API access via SSH tunnel
- **Service Discovery**: Automatic detection of running containers
- **Configuration Storage**: Local config files with remote sync capability

### 8. Testing Strategy
- **Unit Tests**: Test individual components and services
- **Integration Tests**: Test SSH connections, Docker API interactions
- **Mock Testing**: Mock remote services for local development
- **Coverage Goals**: 90%+ test coverage for core functionality
- **CI/CD**: GitHub Actions for automated testing (if repository is public)

### 9. Development Workflow
1. **Local Setup**: Python venv with all dependencies
2. **Mock Mode**: Run locally with mocked remote services
3. **Testing**: Comprehensive test suite before deployment
4. **Staging**: Deploy to test container before production
5. **Production**: Deploy to port 100 on logan-GL502VS

### 10. Security Considerations
- **SSH Key Management**: Secure key storage and rotation
- **Access Control**: Basic authentication for dashboard access
- **Input Validation**: Sanitize all user inputs
- **HTTPS**: SSL/TLS encryption for web interface
- **Audit Logging**: Log all management actions

## Success Criteria
1. **Functional**: Successfully manage all target containers remotely
2. **Reliable**: 99%+ uptime with proper error handling
3. **Fast**: Sub-second response times for most operations
4. **Maintainable**: Clean, documented, tested codebase
5. **User-Friendly**: Intuitive interface requiring minimal training

## Getting Started
1. Set up Python virtual environment
2. Install development dependencies
3. Configure SSH access to remote host
4. Implement core container discovery
5. Build basic web interface
6. Add container management features
7. Implement monitoring and alerting
8. Create comprehensive test suite
9. Deploy and validate functionality

This project will serve as the central command center for the entire Docker infrastructure, providing a single pane of glass for monitoring and managing all containerized services.
