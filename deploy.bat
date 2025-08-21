@echo off
REM Windows deployment script for Docker Dashboard

set REMOTE_USER=logan
set REMOTE_HOST=logan-GL502VS
set APP_NAME=docker-dashboard
set IMAGE_NAME=dashboard
set TARGET_PORT=100

echo Docker Dashboard - Windows Deployment Script
echo ============================================

echo [INFO] Starting deployment process...

REM Check if Docker is available
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not in PATH
    exit /b 1
)

echo [INFO] Docker found, proceeding with deployment...

REM Build the Docker image
echo [INFO] Building Docker image...
docker build -t %IMAGE_NAME%:latest .
if errorlevel 1 (
    echo [ERROR] Failed to build Docker image
    exit /b 1
)

echo [INFO] Docker image built successfully

REM Save image to tar file for transfer
echo [INFO] Saving Docker image to tar file...
docker save %IMAGE_NAME%:latest -o dashboard.tar
if errorlevel 1 (
    echo [ERROR] Failed to save Docker image
    exit /b 1
)

echo [INFO] Docker image saved to dashboard.tar

REM Transfer files to remote server using scp
echo [INFO] Transferring files to remote server...
scp dashboard.tar docker-compose.yml %REMOTE_USER%@%REMOTE_HOST%:~/
if errorlevel 1 (
    echo [ERROR] Failed to transfer files
    exit /b 1
)

echo [INFO] Files transferred successfully

REM Connect to remote server and deploy
echo [INFO] Connecting to remote server and deploying...
ssh %REMOTE_USER%@%REMOTE_HOST% "docker load -i dashboard.tar && docker-compose down 2>/dev/null || true && docker-compose up -d && rm dashboard.tar && echo 'Deployment completed!' && echo 'Dashboard accessible at http://'$(hostname -I | cut -d' ' -f1)':100' && docker ps --filter 'name=dashboard'"

if errorlevel 1 (
    echo [ERROR] Deployment failed
    exit /b 1
)

REM Clean up local files
del dashboard.tar

echo [INFO] Deployment completed successfully!
echo [INFO] Dashboard should be accessible at http://%REMOTE_HOST%:%TARGET_PORT%

pause
