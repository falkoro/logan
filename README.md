# Docker Dashboard

A modern, responsive web dashboard for managing Docker containers on remote hosts with real-time monitoring capabilities.

![Dashboard Preview](https://img.shields.io/badge/Status-Ready%20for%20Testing-green)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0+-red)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)

## Features

### 🚀 Container Management
- **Real-time monitoring** of Docker containers
- **Remote container control** via SSH (start, stop, restart)
- **Bulk operations** for multiple containers
- **Container logs** viewing with search and filtering
- **Resource usage tracking** (CPU, memory, network)

### 📊 System Monitoring
- **System metrics** via Glances API integration
- **Real-time charts** for CPU, memory, and network usage
- **Process monitoring** with top processes display
- **System information** overview

### 🎯 Service Management
- **Predefined service management** for common applications:
  - SABnzbd, qBittorrent, Sonarr, Radarr, Jackett, Plex
  - Portainer, Netdata, Heimdall, Glances
- **Service health monitoring** with status indicators
- **Quick access** to service web interfaces

### 💻 Modern Interface
- **Responsive design** built with Tailwind CSS
- **Dark/Light theme** support
- **WebSocket integration** for real-time updates
- **Interactive charts** with Chart.js
- **Mobile-friendly** interface

## Quick Start

### Prerequisites

- Python 3.11+
- SSH access to remote Docker host
- Glances running on remote host (optional but recommended)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd dashboard
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Run the application**
```bash
python run.py
```

The dashboard will be available at `http://localhost:100`

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Using Docker directly

```bash
# Build image
docker build -t docker-dashboard .

# Run container
docker run -d \
  --name docker-dashboard \
  -p 100:100 \
  -e REMOTE_HOST=logan@logan-GL502VS \
  -e GLANCES_HOST=logan-GL502VS \
  -v ~/.ssh:/home/dashboarduser/.ssh:ro \
  docker-dashboard
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_HOST` | `0.0.0.0` | Host to bind the Flask application |
| `FLASK_PORT` | `100` | Port to run the application |
| `FLASK_ENV` | `development` | Flask environment (development/production) |
| `REMOTE_HOST` | `logan@logan-GL502VS` | SSH connection string for Docker host |
| `REMOTE_PORT` | `22` | SSH port for remote host |
| `GLANCES_HOST` | `logan-GL502VS` | Hostname for Glances API |
| `GLANCES_PORT` | `61208` | Port for Glances API |

### SSH Configuration

Ensure you have SSH key-based authentication set up:

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key to remote host
ssh-copy-id logan@logan-GL502VS

# Test connection
ssh logan@logan-GL502VS docker ps
```

### Glances Setup (Remote Host)

Install and run Glances on your remote Docker host:

```bash
# Install Glances
pip install glances

# Run Glances web server
glances -w --port 61208

# Or run as Docker container
docker run -d --restart="always" \
  -p 61208:61208 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  --name glances \
  nicolargo/glances:latest -w
```

## Project Structure

```
dashboard/
├── app/                      # Application package
│   ├── __init__.py          # Flask app factory
│   ├── config/              # Configuration modules
│   ├── models/              # Data models
│   ├── services/            # Business logic services
│   ├── api/                 # REST API endpoints
│   ├── templates/           # Jinja2 templates
│   └── static/              # Static assets (CSS, JS)
├── tests/                   # Test suite
├── run.py                   # Application entry point
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker build configuration
├── docker-compose.yml      # Docker Compose configuration
└── README.md               # This file
```

## API Endpoints

### Containers
- `GET /api/containers/` - List all containers
- `GET /api/containers/<id>` - Get container details
- `POST /api/containers/<id>/start` - Start container
- `POST /api/containers/<id>/stop` - Stop container
- `POST /api/containers/<id>/restart` - Restart container
- `GET /api/containers/<id>/logs` - Get container logs
- `POST /api/containers/bulk/start` - Start multiple containers
- `POST /api/containers/bulk/stop` - Stop multiple containers
- `POST /api/containers/bulk/restart` - Restart multiple containers

### System
- `GET /api/system/info` - Get system information
- `GET /api/system/metrics` - Get system metrics
- `GET /api/system/processes` - Get running processes

### Health
- `GET /api/health` - Application health check

## Development

### Setting up Development Environment

1. **Install development dependencies**
```bash
pip install -r requirements-dev.txt
```

2. **Run tests**
```bash
pytest
```

3. **Code formatting**
```bash
black app/ tests/
flake8 app/ tests/
```

4. **Run with debug mode**
```bash
export FLASK_DEBUG=True
python run.py
```

### Adding New Features

1. **Models** - Add data models in `app/models/`
2. **Services** - Add business logic in `app/services/`
3. **API** - Add endpoints in `app/api/`
4. **Frontend** - Add templates in `app/templates/` and JS in `app/static/js/`
5. **Tests** - Add tests in `tests/`

## Monitoring Integration

### Supported Services

The dashboard automatically detects and provides special handling for these services:

- **SABnzbd** - Usenet downloader
- **qBittorrent** - BitTorrent client
- **Sonarr** - TV series management
- **Radarr** - Movie management
- **Jackett** - Indexer proxy
- **Plex** - Media server
- **Portainer** - Docker management UI
- **Netdata** - System monitoring
- **Heimdall** - Application dashboard
- **Glances** - System monitoring

### Adding Custom Services

To add support for additional services, modify the `TARGET_SERVICES` list in `app/static/js/services.js` and add appropriate service configuration in the `getServiceConfig()` function.

## Troubleshooting

### Common Issues

**1. SSH Connection Failed**
- Verify SSH key authentication is set up
- Check remote host is accessible: `ssh logan@logan-GL502VS`
- Ensure user has Docker permissions: `sudo usermod -aG docker logan`

**2. Glances API Unavailable**
- Check if Glances is running on remote host: `curl http://logan-GL502VS:61208/api/3/system`
- Verify port 61208 is accessible
- Check firewall settings on remote host

**3. Container Operations Fail**
- Verify Docker daemon is running on remote host
- Check user permissions for Docker commands
- Review application logs: `docker-compose logs -f`

**4. WebSocket Connection Issues**
- Check browser console for WebSocket errors
- Verify no proxy/firewall blocking WebSocket connections
- Try refreshing the page

### Logging

Application logs are available in:
- Console output when running directly
- `logs/` directory when running with Docker
- Docker logs: `docker-compose logs -f docker-dashboard`

## Security Considerations

- **SSH Keys**: Use key-based authentication instead of passwords
- **Firewall**: Limit access to dashboard port (100) to trusted networks
- **HTTPS**: Use a reverse proxy (nginx, traefik) with SSL certificates
- **User Access**: Run application as non-root user in Docker
- **Environment Variables**: Never commit sensitive values to version control

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Flask** - Web framework
- **Tailwind CSS** - CSS framework
- **Chart.js** - Charting library
- **Socket.IO** - Real-time communication
- **Glances** - System monitoring
- **Docker** - Containerization platform

## Support

If you encounter any issues or have questions, please:
1. Check the [Troubleshooting](#troubleshooting) section
2. Search existing [issues](https://github.com/your-repo/issues)
3. Create a new issue with detailed information about your problem

---

**Made with ❤️ for Docker container management**
