# Logan Dashboard 🚀

A modern, responsive Docker management dashboard optimized for 1080p displays. Logan Dashboard provides real-time monitoring and control of Docker containers on remote servers via SSH.

![Logan Dashboard](https://img.shields.io/badge/Status-Active-brightgreen) ![Docker](https://img.shields.io/badge/Docker-Ready-blue) ![Python](https://img.shields.io/badge/Python-3.11+-blue) ![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

### 🖥️ 1080p Optimized Interface
- **Perfect Screen Fit**: Designed specifically for 1920×1080 displays
- **Compact Layout**: No scrolling needed, all information at a glance
- **Responsive Design**: Adapts to different screen sizes

### 📊 Real-time Monitoring
- **System Metrics**: Live CPU, Memory, and Disk usage charts
- **Container Status**: Real-time Docker container monitoring
- **Service Health**: Monitor specific services on designated ports
- **Activity Logging**: Track all operations and system events

### 🎮 Container Management
- **Start/Stop/Restart**: Full container lifecycle management
- **Bulk Operations**: Manage multiple containers simultaneously
- **Service Discovery**: Automatic detection of running services
- **Port Management**: Monitor services on ports 100-110 + Plex (32400)

### 🔐 Secure Remote Access
- **SSH Integration**: Secure connection to remote Docker hosts
- **Key-based Authentication**: Support for SSH key authentication
- **Encrypted Communication**: All data transfer secured via SSH

## 🏗️ Architecture

```
Logan Dashboard/
├── app/                    # Flask application
│   ├── __init__.py        # Application factory
│   ├── config.py          # Configuration management
│   ├── models/            # Data models
│   ├── services/          # Business logic (SSH, Docker, Monitoring)
│   ├── api/              # REST API endpoints
│   └── templates/        # HTML templates
├── static/               # CSS, JavaScript, images
├── tests/               # Test suite
├── docker-compose.yml   # Production deployment
├── Dockerfile          # Container definition
└── requirements.txt    # Python dependencies
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- SSH access to target server

### 1. Clone the Repository
```bash
git clone https://github.com/falkoro/logan.git
cd logan
```

### 2. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

### 3. Deploy with Docker
```bash
# Build and start the dashboard
docker-compose up -d

# Check status
docker-compose ps
```

### 4. Access Dashboard
Open your browser and navigate to:
- **Local**: http://localhost:100
- **Remote**: http://YOUR_SERVER_IP:100

## ⚙️ Configuration

### Environment Variables
```env
# Server Configuration
SSH_HOST=localhost
SSH_USERNAME=your_username
SSH_PORT=22

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your_secret_key_here

# Dashboard Settings
AUTO_REFRESH=true
REFRESH_INTERVAL=30
```

### Managed Services
Edit `app/config.py` to configure monitored services:
```python
MANAGED_SERVICES = {
    'portainer': {
        'name': 'Portainer',
        'port': 9000,
        'container_name': 'portainer'
    },
    'plex': {
        'name': 'Plex Media Server',
        'port': 32400,
        'container_name': 'plex'
    }
    # Add your services here...
}
```

## 🔧 Development

### Local Development Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run development server
python run.py
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

### Building Docker Image
```bash
# Build image
docker build -t logan-dashboard:latest .

# Run container
docker run -d -p 100:5000 --name logan-dashboard logan-dashboard:latest
```

## 🐳 Docker Deployment

### Production Deployment
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Health Checks
The dashboard includes built-in health checks:
- **Health Endpoint**: `/health`
- **Status Checks**: System metrics, SSH connectivity, Docker daemon
- **Container Health**: Automatic restart on failure

## 📱 API Reference

### System Endpoints
- `GET /api/system/metrics` - System resource usage
- `GET /api/system/health` - Overall system health

### Container Endpoints
- `GET /api/containers` - List all containers
- `POST /api/containers/{id}/start` - Start container
- `POST /api/containers/{id}/stop` - Stop container
- `POST /api/containers/{id}/restart` - Restart container

### Service Endpoints
- `GET /api/services` - List managed services
- `GET /api/services/{service}/status` - Service status

## 🎨 Customization

### Themes and Styling
- CSS files located in `app/static/css/`
- Main styles: `logan-dashboard.css`
- Colors defined in CSS custom properties

### Adding New Services
1. Edit `app/config.py`
2. Add service configuration to `MANAGED_SERVICES`
3. Restart the dashboard

### Custom Monitoring
Extend the `MonitoringService` class in `app/services/monitoring_service.py`

## 🛠️ Troubleshooting

### Common Issues

**Dashboard won't start**
```bash
# Check logs
docker-compose logs dashboard

# Verify SSH connectivity
ssh username@hostname
```

**Services not detected**
```bash
# Check Docker daemon
docker ps

# Verify SSH permissions
ssh -v username@hostname
```

**Port conflicts**
```bash
# Check port usage
netstat -tlnp | grep :100

# Modify port in docker-compose.yml
```

## 📊 Monitoring & Metrics

Logan Dashboard tracks:
- **System Resources**: CPU, Memory, Disk usage
- **Container Metrics**: Status, resource usage, logs
- **Network Activity**: Port status, connectivity
- **Application Performance**: Response times, error rates

## 🔐 Security

### Best Practices
- Use SSH key authentication
- Restrict network access to dashboard port
- Regular updates of base images
- Monitor access logs

### Security Features
- **Encrypted SSH connections**
- **No password storage**
- **Container isolation**
- **Read-only Docker socket access**

## 🚧 Roadmap

- [ ] Multi-server support
- [ ] Advanced alerting system
- [ ] Mobile app companion
- [ ] Plugin architecture
- [ ] Kubernetes integration
- [ ] Performance analytics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/falkoro/logan/issues)
- **Discussions**: [Community support and questions](https://github.com/falkoro/logan/discussions)

## 🎯 Acknowledgments

- Flask framework for the web application
- Chart.js for beautiful metrics visualization
- Docker for containerization
- The open-source community for inspiration

---

**Logan Dashboard** - Docker management made beautiful and efficient! 🚀

Made with ❤️ by [@falkoro](https://github.com/falkoro)
