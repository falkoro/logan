# Logan Dashboard - Docker Hub Deployment

## Quick Start with Docker Hub

The easiest way to deploy Logan Dashboard is using the pre-built Docker image from Docker Hub.

### 🚀 One-Command Deployment

```bash
# Pull and run the latest Logan Dashboard
docker run -d \
  --name logan-dashboard \
  -p 100:5000 \
  -e SSH_HOST=localhost \
  -e SSH_USERNAME=your_username \
  --restart unless-stopped \
  falkoro/logan-dashboard:latest
```

### 📦 Docker Compose Deployment

1. **Download the compose file:**
```bash
curl -o docker-compose.yml https://raw.githubusercontent.com/falkoro/logan/main/docker-compose.hub.yml
```

2. **Edit environment variables:**
```bash
# Edit the compose file with your settings
nano docker-compose.yml
```

3. **Deploy:**
```bash
docker-compose up -d
```

### ⚙️ Configuration Options

Configure the dashboard using environment variables:

```bash
docker run -d \
  --name logan-dashboard \
  -p 100:5000 \
  -e SSH_HOST=your-server-ip \
  -e SSH_USERNAME=your-username \
  -e SSH_PORT=22 \
  -e FLASK_ENV=production \
  --restart unless-stopped \
  falkoro/logan-dashboard:latest
```

### 🔐 SSH Key Authentication (Recommended)

Mount your SSH keys for passwordless authentication:

```bash
docker run -d \
  --name logan-dashboard \
  -p 100:5000 \
  -v ~/.ssh:/home/dashboard/.ssh:ro \
  -e SSH_HOST=your-server-ip \
  -e SSH_USERNAME=your-username \
  --restart unless-stopped \
  falkoro/logan-dashboard:latest
```

### 🐳 Local Docker Management

To manage Docker containers on the same host:

```bash
docker run -d \
  --name logan-dashboard \
  -p 100:5000 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -e SSH_HOST=localhost \
  -e SSH_USERNAME=root \
  --restart unless-stopped \
  falkoro/logan-dashboard:latest
```

## 🏷️ Available Tags

- `falkoro/logan-dashboard:latest` - Latest stable release
- `falkoro/logan-dashboard:main` - Development branch
- `falkoro/logan-dashboard:v1.0.0` - Specific version releases

## 🔄 Updates

Update to the latest version:

```bash
# Pull latest image
docker pull falkoro/logan-dashboard:latest

# Restart container with new image
docker-compose down && docker-compose up -d
```

## 📋 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SSH_HOST` | `localhost` | Target server hostname/IP |
| `SSH_USERNAME` | `logan` | SSH username |
| `SSH_PORT` | `22` | SSH port |
| `FLASK_ENV` | `production` | Flask environment |
| `SECRET_KEY` | *auto-generated* | Flask secret key |
| `AUTO_REFRESH` | `true` | Enable auto-refresh |
| `REFRESH_INTERVAL` | `30` | Refresh interval (seconds) |

## 🏥 Health Checks

The container includes health checks:

```bash
# Check container health
docker ps

# View health check logs
docker inspect logan-dashboard | grep Health -A 10
```

## 📊 Monitoring

Access your dashboard at:
- **Local**: http://localhost:100
- **Remote**: http://YOUR_SERVER_IP:100

## 🛠️ Troubleshooting

**Container won't start:**
```bash
docker logs logan-dashboard
```

**SSH connection issues:**
```bash
# Test SSH from container
docker exec logan-dashboard ssh -v username@hostname
```

**Port conflicts:**
```bash
# Use different port
docker run -p 8080:5000 falkoro/logan-dashboard:latest
```

## 🔧 Advanced Configuration

### Custom Services Configuration

Create a custom config file and mount it:

```bash
# Create config
cat > config.py << EOF
MANAGED_SERVICES = {
    'custom_service': {
        'name': 'My Custom Service',
        'port': 8080,
        'container_name': 'my-service'
    }
}
EOF

# Mount config
docker run -d \
  --name logan-dashboard \
  -p 100:5000 \
  -v $(pwd)/config.py:/app/app/config.py:ro \
  falkoro/logan-dashboard:latest
```

### Reverse Proxy Setup

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name dashboard.yourdomain.com;

    location / {
        proxy_pass http://localhost:100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

**Ready to manage your Docker infrastructure with style!** 🚀
