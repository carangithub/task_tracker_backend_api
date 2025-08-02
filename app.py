import os
import logging
from datetime import datetime
from flask import Flask, jsonify, request
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
        logger.warning("Starting server without database connection for documentation access")
        app.config["task_service"] = None
    
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
            if task_service is None:
                return jsonify({
                    'service': 'Task Tracker API',
                    'status': 'running',
                    'timestamp': datetime.utcnow().isoformat(),
                    'uptime': 'Available',
                    'total_tasks': 'N/A - Database not connected',
                    'version': '1.0.0'
                }), 200
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
        if request.args.get('format') == 'json':
            docs = {
                "service": "Task Tracker Backend API",
                "version": "1.0.0",
                "description": "A RESTful API for managing tasks with CRUD operations, filtering, and export functionality",
                "base_url": f"http://{request.host}",
                "endpoints": {
                    "health_status": {
                        "path": "/health",
                        "method": "GET",
                        "description": "Check API health and database connectivity"
                    }
                }
            }
            return jsonify(docs), 200
        
        base_url = f"http://{request.host}"
        html_doc = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Tracker API Documentation</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .nav {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .nav h3 {{
            margin-top: 0;
            color: #667eea;
        }}
        .nav a {{
            color: #667eea;
            text-decoration: none;
            margin-right: 20px;
            font-weight: 500;
        }}
        .nav a:hover {{
            text-decoration: underline;
        }}
        .section {{
            background: white;
            padding: 30px;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .endpoint {{
            border: 1px solid #e9ecef;
            border-radius: 8px;
            margin-bottom: 25px;
            overflow: hidden;
        }}
        .endpoint-header {{
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 1px solid #e9ecef;
        }}
        .method {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 0.9em;
            margin-right: 10px;
        }}
        .method.get {{ background: #d4edda; color: #155724; }}
        .method.post {{ background: #d1ecf1; color: #0c5460; }}
        .method.put {{ background: #fff3cd; color: #856404; }}
        .method.delete {{ background: #f8d7da; color: #721c24; }}
        .endpoint-path {{
            font-family: 'Courier New', monospace;
            font-size: 1.1em;
            font-weight: bold;
            color: #495057;
        }}
        .endpoint-content {{
            padding: 20px;
        }}
        .code-block {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            margin: 10px 0;
            overflow-x: auto;
        }}
        .highlight {{
            background: #fff3cd;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid #ffc107;
            margin: 15px 0;
        }}
        .parameter {{
            background: #f8f9fa;
            border-radius: 4px;
            padding: 10px;
            margin: 5px 0;
            border-left: 3px solid #667eea;
        }}
        .status-indicator {{
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        .status-healthy {{ background: #28a745; }}
        .status-warning {{ background: #ffc107; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            font-size: 0.8em;
            border-radius: 12px;
            background: #667eea;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Task Tracker API</h1>
        <p>RESTful API for managing tasks with CRUD operations, filtering, and export functionality</p>
        <p><strong>Version:</strong> 1.0.0 | <strong>Base URL:</strong> {base_url}</p>
    </div>

    <div class="nav">
        <h3>📖 Quick Navigation</h3>
        <a href="#overview">Overview</a>
        <a href="#endpoints">API Endpoints</a>
        <a href="#models">Data Models</a>
        <a href="#errors">Error Codes</a>
        <a href="#setup">Environment Setup</a>
        <a href="#examples">Examples</a>
    </div>

    <div id="overview" class="section">
        <h2>📋 Overview</h2>
        <p>The Task Tracker API provides a comprehensive solution for managing tasks with the following capabilities:</p>
        <ul>
            <li><strong>CRUD Operations:</strong> Create, read, update, and delete tasks</li>
            <li><strong>Advanced Filtering:</strong> Filter by priority, status, and due dates</li>
            <li><strong>Due Date Monitoring:</strong> Get tasks due within specified timeframes</li>
            <li><strong>CSV Export:</strong> Export all tasks to CSV format</li>
            <li><strong>Health Monitoring:</strong> Built-in health checks and status endpoints</li>
        </ul>
        
        <div class="highlight">
            <strong>💡 Pro Tip:</strong> All datetime fields use ISO 8601 format (e.g., "2024-12-31T23:59:59"). 
            Add <code>?format=json</code> to this URL to get machine-readable documentation.
        </div>
    </div>

    <div id="endpoints" class="section">
        <h2>🔗 API Endpoints</h2>
        
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method get">GET</span>
                <span class="endpoint-path">/health</span>
            </div>
            <div class="endpoint-content">
                <p><strong>Description:</strong> Check API health and database connectivity</p>
                <p><strong>Returns:</strong> Health status with database connection info</p>
                <div class="code-block">
curl {base_url}/health</div>
                <p><strong>Response Example:</strong></p>
                <div class="code-block">{{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "database": "connected",
  "version": "1.0.0"
}}</div>
            </div>
        </div>

        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method get">GET</span>
                <span class="endpoint-path">/status</span>
            </div>
            <div class="endpoint-content">
                <p><strong>Description:</strong> Get service status and total task count</p>
                <div class="code-block">
curl {base_url}/status</div>
            </div>
        </div>

        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method post">POST</span>
                <span class="endpoint-path">/tasks</span>
            </div>
            <div class="endpoint-content">
                <p><strong>Description:</strong> Create a new task</p>
                <p><strong>Content-Type:</strong> application/json</p>
                
                <h4>Required Fields:</h4>
                <div class="parameter"><strong>title:</strong> string - Task title</div>
                <div class="parameter"><strong>description:</strong> string - Task description</div>
                <div class="parameter"><strong>priority:</strong> string - One of: low, medium, high</div>
                <div class="parameter"><strong>status:</strong> string - One of: TODO, IN_PROGRESS, COMPLETED</div>
                <div class="parameter"><strong>due_date:</strong> string - ISO datetime format</div>
                
                <h4>Optional Fields:</h4>
                <div class="parameter"><strong>tags:</strong> array - List of string tags</div>

                <p><strong>Example Request:</strong></p>
                <div class="code-block">
curl -X POST {base_url}/tasks \\
  -H "Content-Type: application/json" \\
  -d '{{
    "title": "Complete project documentation",
    "description": "Write comprehensive API documentation",
    "priority": "high",
    "status": "TODO",
    "due_date": "2024-12-31T23:59:59",
    "tags": ["documentation", "urgent"]
  }}'</div>
            </div>
        </div>

        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method get">GET</span>
                <span class="endpoint-path">/tasks</span>
            </div>
            <div class="endpoint-content">
                <p><strong>Description:</strong> Retrieve all tasks with optional filtering</p>
                
                <h4>Query Parameters (all optional):</h4>
                <div class="parameter"><strong>priority:</strong> Filter by priority (low, medium, high)</div>
                <div class="parameter"><strong>status:</strong> Filter by status (TODO, IN_PROGRESS, COMPLETED)</div>
                <div class="parameter"><strong>due_date_before:</strong> ISO datetime - tasks due before this date</div>
                <div class="parameter"><strong>due_date_after:</strong> ISO datetime - tasks due after this date</div>

                <p><strong>Examples:</strong></p>
                <div class="code-block">
# Get all high priority TODO tasks
curl "{base_url}/tasks?priority=high&status=TODO"

# Get tasks due before end of year
curl "{base_url}/tasks?due_date_before=2024-12-31T23:59:59"</div>
            </div>
        </div>

        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method get">GET</span>
                <span class="endpoint-path">/tasks/{{task_id}}</span>
            </div>
            <div class="endpoint-content">
                <p><strong>Description:</strong> Retrieve a specific task by ID</p>
                <div class="parameter"><strong>task_id:</strong> MongoDB ObjectId (24 character hex string)</div>
                <div class="code-block">
curl {base_url}/tasks/65a1b2c3d4e5f6789abcdef0</div>
            </div>
        </div>

        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method put">PUT</span>
                <span class="endpoint-path">/tasks/{{task_id}}</span>
            </div>
            <div class="endpoint-content">
                <p><strong>Description:</strong> Update an existing task</p>
                <p><strong>Note:</strong> All fields are optional. Only include fields you want to update.</p>
                <div class="code-block">
curl -X PUT {base_url}/tasks/65a1b2c3d4e5f6789abcdef0 \\
  -H "Content-Type: application/json" \\
  -d '{{
    "status": "COMPLETED",
    "priority": "medium"
  }}'</div>
            </div>
        </div>

        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method delete">DELETE</span>
                <span class="endpoint-path">/tasks/{{task_id}}</span>
            </div>
            <div class="endpoint-content">
                <p><strong>Description:</strong> Delete a task by ID</p>
                <p><strong>Returns:</strong> 204 No Content on success</p>
                <div class="code-block">
curl -X DELETE {base_url}/tasks/65a1b2c3d4e5f6789abcdef0</div>
            </div>
        </div>

        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method get">GET</span>
                <span class="endpoint-path">/tasks/due</span>
            </div>
            <div class="endpoint-content">
                <p><strong>Description:</strong> Get tasks due within specified hours</p>
                <div class="parameter"><strong>hours:</strong> integer (optional, default: 24) - Number of hours to look ahead</div>
                <div class="code-block">
# Get tasks due in next 48 hours
curl "{base_url}/tasks/due?hours=48"</div>
            </div>
        </div>

        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method get">GET</span>
                <span class="endpoint-path">/tasks/export/csv</span>
            </div>
            <div class="endpoint-content">
                <p><strong>Description:</strong> Export all tasks as CSV file</p>
                <p><strong>Returns:</strong> CSV file download with filename 'tasks.csv'</p>
                <div class="code-block">
curl {base_url}/tasks/export/csv -o tasks.csv</div>
            </div>
        </div>
    </div>

    <div id="models" class="section">
        <h2>📊 Data Models</h2>
        
        <h3>Task Object</h3>
        <table>
            <thead>
                <tr>
                    <th>Field</th>
                    <th>Type</th>
                    <th>Description</th>
                    <th>Required</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><code>id</code></td>
                    <td>string</td>
                    <td>Auto-generated MongoDB ObjectId</td>
                    <td><span class="badge">Auto</span></td>
                </tr>
                <tr>
                    <td><code>title</code></td>
                    <td>string</td>
                    <td>Task title</td>
                    <td><span class="badge">Yes</span></td>
                </tr>
                <tr>
                    <td><code>description</code></td>
                    <td>string</td>
                    <td>Task description</td>
                    <td><span class="badge">Yes</span></td>
                </tr>
                <tr>
                    <td><code>priority</code></td>
                    <td>string</td>
                    <td>Priority level: low, medium, high</td>
                    <td><span class="badge">Yes</span></td>
                </tr>
                <tr>
                    <td><code>status</code></td>
                    <td>string</td>
                    <td>Current status: TODO, IN_PROGRESS, COMPLETED</td>
                    <td><span class="badge">Yes</span></td>
                </tr>
                <tr>
                    <td><code>due_date</code></td>
                    <td>string</td>
                    <td>ISO datetime when task is due</td>
                    <td><span class="badge">Yes</span></td>
                </tr>
                <tr>
                    <td><code>created_at</code></td>
                    <td>string</td>
                    <td>ISO datetime when task was created</td>
                    <td><span class="badge">Auto</span></td>
                </tr>
                <tr>
                    <td><code>tags</code></td>
                    <td>array</td>
                    <td>List of string tags</td>
                    <td><span class="badge">No</span></td>
                </tr>
            </tbody>
        </table>
    </div>

    <div id="errors" class="section">
        <h2>⚠️ Error Responses</h2>
        <table>
            <thead>
                <tr>
                    <th>Code</th>
                    <th>Status</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>200</td>
                    <td>OK</td>
                    <td>Request successful</td>
                </tr>
                <tr>
                    <td>201</td>
                    <td>Created</td>
                    <td>Resource created successfully</td>
                </tr>
                <tr>
                    <td>204</td>
                    <td>No Content</td>
                    <td>Resource deleted successfully</td>
                </tr>
                <tr>
                    <td>400</td>
                    <td>Bad Request</td>
                    <td>Invalid input parameters or malformed request</td>
                </tr>
                <tr>
                    <td>404</td>
                    <td>Not Found</td>
                    <td>Resource not found</td>
                </tr>
                <tr>
                    <td>500</td>
                    <td>Internal Server Error</td>
                    <td>Server error occurred</td>
                </tr>
                <tr>
                    <td>503</td>
                    <td>Service Unavailable</td>
                    <td>Database connection issues</td>
                </tr>
            </tbody>
        </table>
    </div>

    <div id="setup" class="section">
        <h2>⚙️ Environment Setup</h2>
        <p>Configure these environment variables for your deployment:</p>
        
        <table>
            <thead>
                <tr>
                    <th>Variable</th>
                    <th>Description</th>
                    <th>Default</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><code>MONGODB_URI</code></td>
                    <td>MongoDB connection string</td>
                    <td>mongodb://localhost:27017/</td>
                </tr>
                <tr>
                    <td><code>DATABASE_NAME</code></td>
                    <td>Database name</td>
                    <td>tasktracker</td>
                </tr>
                <tr>
                    <td><code>SECRET_KEY</code></td>
                    <td>Flask secret key for sessions</td>
                    <td>your-secret-key-change-in-production</td>
                </tr>
                <tr>
                    <td><code>CORS_ORIGINS</code></td>
                    <td>Allowed CORS origins</td>
                    <td>* (all origins)</td>
                </tr>
                <tr>
                    <td><code>LOG_LEVEL</code></td>
                    <td>Logging level</td>
                    <td>INFO</td>
                </tr>
                <tr>
                    <td><code>PORT</code></td>
                    <td>Server port</td>
                    <td>5000</td>
                </tr>
                <tr>
                    <td><code>HOST</code></td>
                    <td>Server host</td>
                    <td>0.0.0.0</td>
                </tr>
            </tbody>
        </table>
    </div>

    <div id="examples" class="section">
        <h2>💡 Complete Examples</h2>
        
        <h3>Create and Manage a Task Workflow</h3>
        <div class="code-block">
# 1. Create a new task
curl -X POST {base_url}/tasks \\
  -H "Content-Type: application/json" \\
  -d '{{
    "title": "Review API documentation",
    "description": "Review and update the API documentation for accuracy",
    "priority": "medium",
    "status": "TODO",
    "due_date": "2024-12-31T17:00:00",
    "tags": ["documentation", "review"]
  }}'

# 2. Get all high priority tasks
curl "{base_url}/tasks?priority=high"

# 3. Update task status to in progress
curl -X PUT {base_url}/tasks/[TASK_ID] \\
  -H "Content-Type: application/json" \\
  -d '{{"status": "IN_PROGRESS"}}'

# 4. Mark task as completed
curl -X PUT {base_url}/tasks/[TASK_ID] \\
  -H "Content-Type: application/json" \\
  -d '{{"status": "COMPLETED"}}'

# 5. Export all tasks to CSV
curl {base_url}/tasks/export/csv -o my_tasks.csv</div>

        <h3>Filtering Examples</h3>
        <div class="code-block">
# Get all completed tasks
curl "{base_url}/tasks?status=COMPLETED"

# Get high priority tasks that are not completed
curl "{base_url}/tasks?priority=high&status=TODO"

# Get tasks due in the next week
curl "{base_url}/tasks/due?hours=168"

# Get tasks due before a specific date
curl "{base_url}/tasks?due_date_before=2024-12-25T00:00:00"</div>
    </div>

    <footer style="text-align: center; margin-top: 40px; padding: 20px; color: #6c757d;">
        <p>📚 Task Tracker API Documentation | Version 1.0.0</p>
        <p>Need help? Check the <a href="/health" style="color: #667eea;">health endpoint</a> or <a href="/status" style="color: #667eea;">status endpoint</a></p>
    </footer>
</body>
</html>
        """
        return html_doc
    
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