import os
import logging
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from controllers.task_controller import task_bp
from services.task_service import TaskService
from werkzeug.exceptions import HTTPException

def create_app():
    app = Flask(__name__)
    
    # Production configurations
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
    app.config['MONGODB_URI'] = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
    app.config['DATABASE_NAME'] = os.environ.get('DATABASE_NAME', 'tasktracker')
    app.config['CORS_ORIGINS'] = os.environ.get('CORS_ORIGINS', '*')
    app.config['LOG_LEVEL'] = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, app.config['LOG_LEVEL']),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log')
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # CORS setup
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Database connection with error handling
    try:
        client = MongoClient(app.config['MONGODB_URI'], serverSelectionTimeoutMS=5000)
        client.server_info()  # Test connection
        db = client[app.config['DATABASE_NAME']]
        app.config["task_service"] = TaskService(db)
        logger.info("Database connection established successfully")
    except ServerSelectionTimeoutError as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise Exception("Database connection failed")
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        try:
            # Test database connection
            client.server_info()
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'database': 'connected',
                'version': '1.0.0'
            }), 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'database': 'disconnected',
                'error': str(e)
            }), 503
    
    # Status endpoint
    @app.route('/status', methods=['GET'])
    def status():
        try:
            task_service = app.config["task_service"]
            total_tasks = len(task_service.repository.get_all())
            return jsonify({
                'service': 'Task Tracker API',
                'status': 'running',
                'timestamp': datetime.utcnow().isoformat(),
                'uptime': 'Available',
                'total_tasks': total_tasks,
                'version': '1.0.0'
            }), 200
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return jsonify({
                'service': 'Task Tracker API',
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }), 500
    
    # Global error handler
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        if isinstance(e, HTTPException):
            return jsonify({
                'error': e.description,
                'status_code': e.code
            }), e.code
        return jsonify({
            'error': 'Internal server error',
            'status_code': 500
        }), 500
    
    # 404 handler
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            'error': 'Endpoint not found',
            'status_code': 404
        }), 404
    
    # Register blueprints
    app.register_blueprint(task_bp)
    
    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host=host, port=port, debug=debug)