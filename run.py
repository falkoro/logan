"""
Application entry point
"""
import os
import logging
from app import create_app

# Create Flask application
app = create_app()

def main():
    """Main application entry point"""
    try:
        # Get configuration from app config
        host = app.config.get('HOST', '0.0.0.0')
        port = app.config.get('PORT', 5000)
        debug = app.config.get('DEBUG', False)
        
        app.logger.info(f"Starting LoganGemma Dashboard on {host}:{port}")
        app.logger.info(f"Remote Docker host: {app.config.get('REMOTE_HOST', 'unknown')}")
        app.logger.info(f"Glances API: {app.config.get('GLANCES_HOST', 'unknown')}:{app.config.get('GLANCES_PORT', 'unknown')}")
        
        # Use regular Flask server for now (without WebSocket support)
        app.logger.info("Starting with Flask development server (WebSockets disabled)")
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug
        )
        
    except KeyboardInterrupt:
        app.logger.info("Application stopped by user")
    except Exception as e:
        app.logger.error(f"Failed to start application: {e}")
        raise

if __name__ == '__main__':
    main()
