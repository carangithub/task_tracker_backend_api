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

    # API Documentation endpoint
    @app.route('/', methods=['GET'])
    @app.route('/docs', methods=['GET'])
    def api_documentation():
        docs = {
            "service": "Task Tracker Backend API",
            "version": "1.0.0",
            "description": "A RESTful API for managing tasks with CRUD operations, filtering, and export functionality",
            "base_url": f"http://{request.host}",
            "endpoints": {
                "health_status": {
                    "path": "/health",
                    "method": "GET",
                    "description": "Check API health and database connectivity",
                    "response_example": {
                        "status": "healthy",
                        "timestamp": "2024-01-01T12:00:00",
                        "database": "connected",
                        "version": "1.0.0"
                    }
                },
                "service_status": {
                    "path": "/status",
                    "method": "GET",
                    "description": "Get service status and total task count",
                    "response_example": {
                        "service": "Task Tracker API",
                        "status": "running",
                        "timestamp": "2024-01-01T12:00:00",
                        "total_tasks": 25
                    }
                },
                "create_task": {
                    "path": "/tasks",
                    "method": "POST",
                    "description": "Create a new task",
                    "request_body": {
                        "title": "string (required) - Task title",
                        "description": "string (required) - Task description",
                        "priority": "string (required) - One of: low, medium, high",
                        "status": "string (required) - One of: TODO, IN_PROGRESS, COMPLETED",
                        "due_date": "string (required) - ISO format datetime (e.g., '2024-12-31T23:59:59')",
                        "tags": "array of strings (optional) - Task tags"
                    },
                    "example_request": {
                        "title": "Complete project documentation",
                        "description": "Write comprehensive API documentation",
                        "priority": "high",
                        "status": "TODO",
                        "due_date": "2024-12-31T23:59:59",
                        "tags": ["documentation", "urgent"]
                    }
                },
                "get_all_tasks": {
                    "path": "/tasks",
                    "method": "GET",
                    "description": "Retrieve all tasks with optional filtering",
                    "query_parameters": {
                        "priority": "string (optional) - Filter by priority: low, medium, high",
                        "status": "string (optional) - Filter by status: TODO, IN_PROGRESS, COMPLETED",
                        "due_date_before": "string (optional) - ISO datetime, get tasks due before this date",
                        "due_date_after": "string (optional) - ISO datetime, get tasks due after this date"
                    },
                    "example_url": "/tasks?priority=high&status=TODO&due_date_before=2024-12-31T23:59:59"
                },
                "get_task_by_id": {
                    "path": "/tasks/{task_id}",
                    "method": "GET",
                    "description": "Retrieve a specific task by ID",
                    "path_parameters": {
                        "task_id": "string (required) - MongoDB ObjectId of the task"
                    },
                    "example_url": "/tasks/65a1b2c3d4e5f6789abcdef0"
                },
                "update_task": {
                    "path": "/tasks/{task_id}",
                    "method": "PUT",
                    "description": "Update an existing task",
                    "path_parameters": {
                        "task_id": "string (required) - MongoDB ObjectId of the task"
                    },
                    "request_body": "Same as create_task, but all fields are optional",
                    "example_request": {
                        "status": "COMPLETED",
                        "priority": "medium"
                    }
                },
                "delete_task": {
                    "path": "/tasks/{task_id}",
                    "method": "DELETE",
                    "description": "Delete a task by ID",
                    "path_parameters": {
                        "task_id": "string (required) - MongoDB ObjectId of the task"
                    },
                    "response": "204 No Content on success"
                },
                "get_due_tasks": {
                    "path": "/tasks/due",
                    "method": "GET",
                    "description": "Get tasks due within specified hours",
                    "query_parameters": {
                        "hours": "integer (optional, default: 24) - Number of hours to look ahead"
                    },
                    "example_url": "/tasks/due?hours=48"
                },
                "export_tasks_csv": {
                    "path": "/tasks/export/csv",
                    "method": "GET",
                    "description": "Export all tasks as CSV file",
                    "response": "CSV file download with filename 'tasks.csv'"
                }
            },
            "data_models": {
                "task_object": {
                    "id": "string - Auto-generated MongoDB ObjectId",
                    "title": "string - Task title",
                    "description": "string - Task description",
                    "priority": "string - Priority level (low/medium/high)",
                    "status": "string - Current status (TODO/IN_PROGRESS/COMPLETED)",
                    "due_date": "string - ISO datetime when task is due",
                    "created_at": "string - ISO datetime when task was created",
                    "tags": "array - List of string tags"
                }
            },
            "error_responses": {
                "400": "Bad Request - Invalid input parameters",
                "404": "Not Found - Resource not found",
                "500": "Internal Server Error - Server error",
                "503": "Service Unavailable - Database connection issues"
            },
            "environment_variables": {
                "MONGODB_URI": "MongoDB connection string (default: mongodb://localhost:27017/)",
                "DATABASE_NAME": "Database name (default: tasktracker)",
                "SECRET_KEY": "Flask secret key for sessions",
                "CORS_ORIGINS": "Allowed CORS origins (default: *)",
                "LOG_LEVEL": "Logging level (default: INFO)",
                "PORT": "Server port (default: 5000)",
                "HOST": "Server host (default: 0.0.0.0)"
            }
        }
        return jsonify(docs), 200
    
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