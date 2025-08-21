"""Test configuration."""
import pytest
import os
import tempfile
from app import create_test_app

@pytest.fixture
def app():
    """Create and configure a test app."""
    app = create_test_app()
    
    # Create a temporary file for the database
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    
    yield app
    
    # Clean up
    os.close(db_fd)
    os.unlink(app.config['DATABASE'])

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test runner."""
    return app.test_cli_runner()
