"""Unit tests for container model."""
import pytest
from datetime import datetime
from app.models.container import ContainerModel

def test_container_model_creation():
    """Test ContainerModel creation."""
    container = ContainerModel(
        id='test-id',
        name='test-container',
        image='test-image:latest',
        status='running',
        state='running',
        created=datetime.now()
    )
    
    assert container.id == 'test-id'
    assert container.name == 'test-container'
    assert container.image == 'test-image:latest'
    assert container.is_running is True

def test_container_model_to_dict():
    """Test ContainerModel to_dict method."""
    container = ContainerModel(
        id='test-id',
        name='test-container',
        image='test-image:latest',
        status='running',
        state='running',
        created=datetime.now(),
        service_port=8080
    )
    
    container_dict = container.to_dict()
    
    assert container_dict['id'] == 'test-id'
    assert container_dict['name'] == 'test-container'
    assert container_dict['is_running'] is True
    assert container_dict['main_port'] == 8080

def test_container_model_web_url():
    """Test ContainerModel web_url property."""
    container = ContainerModel(
        id='test-id',
        name='test-container',
        image='test-image:latest',
        status='running',
        state='running',
        created=datetime.now(),
        service_port=8080
    )
    
    assert container.web_url == 'http://logan-GL502VS:8080'

def test_container_model_from_docker_container():
    """Test ContainerModel.from_docker_container class method."""
    docker_data = {
        'Id': 'container-id-123',
        'Name': '/test-container',
        'Config': {
            'Image': 'test-image:latest',
            'Env': ['PATH=/usr/local/bin', 'ENV_VAR=value']
        },
        'State': {
            'Status': 'running'
        },
        'Created': '2023-01-01T10:00:00Z',
        'NetworkSettings': {
            'Ports': {
                '8080/tcp': [{'HostIp': '0.0.0.0', 'HostPort': '8080'}]
            }
        }
    }
    
    service_config = {
        'name': 'Test Service',
        'port': 8080,
        'category': 'test',
        'vpn_required': False
    }
    
    container = ContainerModel.from_docker_container(docker_data, service_config)
    
    assert container.id == 'container-id-123'
    assert container.name == 'test-container'
    assert container.service_name == 'Test Service'
    assert container.service_port == 8080
    assert 'ENV_VAR' in container.environment
