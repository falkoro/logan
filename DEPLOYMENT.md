# Docker Dashboard - Deployment Guide

## Overview
This guide provides instructions for deploying the Docker Dashboard to your remote server `logan@logan-GL502VS`.

## Prerequisites

### Local Machine Requirements
1. **Docker**: Install Docker Desktop for Windows
   - Download from: https://www.docker.com/products/docker-desktop
   - Ensure Docker daemon is running
2. **SSH Client**: Windows 10/11 includes OpenSSH by default
3. **Git Bash** (optional): For running shell scripts

### Remote Server Requirements
1. **Docker**: Ensure Docker is installed on `logan-GL502VS`
2. **SSH Access**: SSH key-based authentication recommended
3. **Port 100**: Available for the dashboard

## Deployment Options

### Option 1: Automated Deployment (Recommended)

#### For Windows PowerShell/CMD:
```batch
# Navigate to project directory
cd c:\Users\falk\dashboard

# Run Windows deployment script
deploy.bat
```

#### For Git Bash/WSL:
```bash
# Navigate to project directory
cd /c/Users/falk/dashboard

# Make script executable and run
chmod +x deploy.sh
./deploy.sh
```

### Option 2: Manual Deployment

#### Step 1: Build Docker Image
```bash
# In project directory
docker build -t dashboard:latest .
```

#### Step 2: Save and Transfer Image
```bash
# Save image to tar file
docker save dashboard:latest -o dashboard.tar

# Transfer to remote server
scp dashboard.tar docker-compose.yml logan@logan-GL502VS:~/
```

#### Step 3: Deploy on Remote Server
```bash
# SSH to remote server
ssh logan@logan-GL502VS

# Load and run the image
docker load -i dashboard.tar
docker-compose down  # Stop existing containers
docker-compose up -d # Start new containers
rm dashboard.tar     # Clean up
```

## SSH Configuration

### Generate SSH Key (if not already done)
```bash
# Generate new SSH key
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Copy public key to remote server
ssh-copy-id logan@logan-GL502VS
```

### Test SSH Connection
```bash
ssh logan@logan-GL502VS
```

## Verification

After deployment, verify the dashboard is running:

### Check Container Status
```bash
# On remote server
ssh logan@logan-GL502VS
docker ps --filter "name=dashboard"
```

### Access Dashboard
- Open browser and navigate to: `http://logan-GL502VS:100`
- Or use the server's IP address: `http://[SERVER_IP]:100`

### Check Logs
```bash
# View container logs
docker-compose logs dashboard
```

## Configuration

### Environment Variables
The application uses these environment variables (configured in docker-compose.yml):
- `FLASK_ENV=production`
- `SSH_HOST=localhost` (since running on the same server)
- `SSH_USERNAME=logan`
- `SSH_PORT=22`

### Managed Services
The dashboard manages these services by default:
- Portainer (port 9000)
- Services on ports 101-110
- Plex Media Server (port 32400)

To modify services, edit `app/config.py` and rebuild.

## Troubleshooting

### Common Issues

1. **Docker not found**
   - Ensure Docker is installed and running
   - Check PATH includes Docker binaries

2. **SSH connection failed**
   - Verify SSH keys are set up correctly
   - Check remote server is accessible
   - Ensure SSH daemon is running on remote server

3. **Port 100 already in use**
   - Check what's using port 100: `sudo netstat -tlnp | grep :100`
   - Stop conflicting service or change port in docker-compose.yml

4. **Container won't start**
   - Check logs: `docker-compose logs dashboard`
   - Verify SSH connectivity from container to Docker host
   - Ensure all required ports are available

### Health Check
The application includes a health check endpoint:
```bash
curl http://logan-GL502VS:100/health
```

### Reset Deployment
To completely reset the deployment:
```bash
# On remote server
docker-compose down
docker rmi dashboard:latest
docker system prune -f
```

## Security Notes

1. **SSH Keys**: Use key-based authentication instead of passwords
2. **Firewall**: Ensure only necessary ports are open
3. **Updates**: Regularly update the dashboard and underlying system
4. **Monitoring**: Monitor logs for suspicious activity

## Support

If you encounter issues:
1. Check the logs: `docker-compose logs dashboard`
2. Verify network connectivity
3. Ensure all prerequisites are met
4. Check the troubleshooting section above

## Next Steps

After successful deployment:
1. Set up automated backups
2. Configure log rotation
3. Set up monitoring alerts
4. Plan regular updates

The dashboard will be accessible at `http://logan-GL502VS:100` and will provide:
- Real-time container status
- Service management (start/stop/restart)
- System metrics and monitoring
- Activity logs
- Responsive web interface
