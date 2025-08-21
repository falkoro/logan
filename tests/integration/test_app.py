"""Integration tests for Flask application."""
import json
from unittest.mock import patch, MagicMock

def test_health_check(client):
    """Test health check endpoint."""
    with patch('app.ssh_service.is_connected', return_value=True), \
         patch('app.ssh_service.test_docker_access', return_value=True):
        
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['checks']['ssh_connection'] is True
        assert data['checks']['docker_access'] is True

def test_health_check_unhealthy(client):
    """Test health check endpoint when unhealthy."""
    with patch('app.ssh_service.is_connected', return_value=False):
        
        response = client.get('/api/health')
        assert response.status_code == 500
        
        data = json.loads(response.data)
        assert data['status'] == 'unhealthy'

def test_services_endpoint(client):
    """Test services endpoint."""
    response = client.get('/api/services')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'data' in data
    assert isinstance(data['data'], dict)

def test_dashboard_page(client):
    """Test main dashboard page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Docker Dashboard' in response.data

def test_404_error(client):
    """Test 404 error handling."""
    response = client.get('/nonexistent')
    assert response.status_code == 404

def test_api_404_error(client):
    """Test API 404 error handling."""
    response = client.get('/api/nonexistent')
    assert response.status_code == 404
    
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'not found' in data['message'].lower()
