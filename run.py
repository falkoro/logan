"""Application entry point."""
import os
import logging
from app import create_app

logger = logging.getLogger(__name__)

# Create Flask application
app = create_app()

if __name__ == '__main__':
    # Get configuration from environment
    host = app.config.get('HOST', '0.0.0.0')
    port = app.config.get('PORT', 5000)
    debug = app.config.get('DEBUG', False)
    
    logger.info(f"Starting Docker Dashboard on {host}:{port} (debug={debug})")
    
    # Run the application
    app.run(host=host, port=port, debug=debug)
