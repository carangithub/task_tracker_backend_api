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
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Courier New', monospace;
            line-height: 1.5;
            color: #000;
            background-color: #fff;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            border: 2px solid #000;
            padding: 30px;
            margin-bottom: 20px;
            text-align: center;
            background: #000;
            color: #fff;
        }}
        .header h1 {{
            font-size: 24px;
            margin-bottom: 10px;
            font-weight: bold;
        }}
        .header p {{
            font-size: 14px;
            margin: 5px 0;
        }}
        .nav {{
            border: 2px solid #000;
            padding: 20px;
            margin-bottom: 20px;
            background: #fff;
        }}
        .nav h3 {{
            font-size: 16px;
            margin-bottom: 15px;
            font-weight: bold;
        }}
        .nav a {{
            color: #000;
            text-decoration: none;
            margin-right: 20px;
            border-bottom: 1px solid #000;
            padding-bottom: 2px;
        }}
        .nav a:hover {{
            background: #000;
            color: #fff;
            padding: 2px 4px;
        }}
        .section {{
            border: 2px solid #000;
            padding: 25px;
            margin-bottom: 20px;
            background: #fff;
        }}
        .section h2 {{
            font-size: 18px;
            margin-bottom: 15px;
            font-weight: bold;
            border-bottom: 1px solid #000;
            padding-bottom: 5px;
        }}
        .endpoint {{
            border: 1px solid #000;
            margin-bottom: 20px;
            background: #fff;
        }}
        .endpoint-header {{
            background: #000;
            color: #fff;
            padding: 12px 15px;
            font-weight: bold;
        }}
        .method {{
            display: inline-block;
            padding: 2px 8px;
            border: 1px solid #fff;
            margin-right: 10px;
            font-size: 12px;
        }}
        .endpoint-path {{
            font-family: 'Courier New', monospace;
            font-size: 14px;
        }}
        .endpoint-content {{
            padding: 15px;
            border-left: 3px solid #000;
            margin-left: 10px;
        }}
        .code-block {{
            background: #000;
            color: #fff;
            border: 1px solid #000;
            padding: 12px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            margin: 10px 0;
            overflow-x: auto;
        }}
        .parameter {{
            border: 1px solid #000;
            padding: 8px;
            margin: 5px 0;
            background: #fff;
        }}
        .parameter strong {{
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            border: 2px solid #000;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border: 1px solid #000;
            font-size: 12px;
        }}
        th {{
            background: #000;
            color: #fff;
            font-weight: bold;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 6px;
            font-size: 10px;
            border: 1px solid #000;
            background: #000;
            color: #fff;
        }}
        ul {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        li {{
            margin: 5px 0;
        }}
        h3 {{
            font-size: 16px;
            margin: 15px 0 10px 0;
            font-weight: bold;
        }}
        h4 {{
            font-size: 14px;
            margin: 10px 0 5px 0;
            font-weight: bold;
        }}
        p {{
            margin: 8px 0;
            font-size: 13px;
        }}
        code {{
            font-family: 'Courier New', monospace;
            background: #000;
            color: #fff;
            padding: 1px 4px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>TASK TRACKER API</h1>
        <p>RESTful API for managing tasks with CRUD operations, filtering, and export functionality</p>
        <p>Version: 1.0.0 | Base URL: {base_url}</p>
    </div>

    <div class="nav">
        <h3>NAVIGATION</h3>
        <a href="#overview">Overview</a>
        <a href="#endpoints">API Endpoints</a>
        <a href="#models">Data Models</a>
        <a href="#errors">Error Codes</a>
        <a href="#setup">Environment Setup</a>
        <a href="#examples">Examples</a>
    </div>

    <div id="overview" class="section">
        <h2>OVERVIEW</h2>
        <p>The Task Tracker API provides a comprehensive solution for managing tasks with the following capabilities:</p>
        <ul>
            <li>CRUD Operations: Create, read, update, and delete tasks</li>
            <li>Advanced Filtering: Filter by priority, status, and due dates</li>
            <li>Due Date Monitoring: Get tasks due within specified timeframes</li>
            <li>CSV Export: Export all tasks to CSV format</li>
            <li>Health Monitoring: Built-in health checks and status endpoints</li>
        </ul>
        
        <p><strong>Note:</strong> All datetime fields use ISO 8601 format (e.g., "2024-12-31T23:59:59"). Add <code>?format=json</code> to this URL to get machine-readable documentation.</p>
    </div>

    <div id="endpoints" class="section">
        <h2>API ENDPOINTS</h2>
        
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method">GET</span>
                <span class="endpoint-path">/health</span>
            </div>
            <div class="endpoint-content">
                <p><strong>Description:</strong> Check API health and database connectivity</p>
                <p><strong>Returns:</strong> Health status with database connection info</p>
                <div class="code-block">curl {base_url}/health</div>
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
                <span class="method">GET</span>
                <span class="endpoint-path">/status</span>
            </div>
            <div class="endpoint-content">
                <p><strong>Description:</strong> Get service status and total task count</p>
                <div class="code-block">curl {base_url}/status</div>
            </div>
        </div>

        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method">POST</span>
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
                <div class="code-block">curl -X POST {base_url}/tasks \
  -H "Content-Type: application/json" \
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
                <span class="method">GET</span>
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
                <div class="code-block"># Get all high priority TODO tasks
curl "{base_url}/tasks?priority=high&status=TODO"

# Get tasks due before end of year
curl "{base_url}/tasks?due_date_before=2024-12-31T23:59:59"</div>
            </div>
        </div>

        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method">GET</span>
                <span class="endpoint-path">/tasks/{{task_id}}</span>
            </div>
            <div class="endpoint-content">
                <p><strong>Description:</strong> Retrieve a specific task by ID</p>
                <div class="parameter"><strong>task_id:</strong> MongoDB ObjectId (24 character hex string)</div>
                <div class="code-block">curl {base_url}/tasks/65a1b2c3d4e5f6789abcdef0</div>
            </div>
        </div>

        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method">PUT</span>
                <span class="endpoint-path">/tasks/{{task_id}}</span>
            </div>
            <div class="endpoint-content">
                <p><strong>Description:</strong> Update an existing task</p>
                <p><strong>Note:</strong> All fields are optional. Only include fields you want to update.</p>
                <div class="code-block">curl -X PUT {base_url}/tasks/65a1b2c3d4e5f6789abcdef0 \
  -H "Content-Type: application/json" \
  -d '{{
    "status": "COMPLETED",
    "priority": "medium"
  }}'</div>
            </div>
        </div>

        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method">DELETE</span>
                <span class="endpoint-path">/tasks/{{task_id}}</span>
            </div>
            <div class="endpoint-content">
                <p><strong>Description:</strong> Delete a task by ID</p>
                <p><strong>Returns:</strong> 204 No Content on success</p>
                <div class="code-block">curl -X DELETE {base_url}/tasks/65a1b2c3d4e5f6789abcdef0</div>
            </div>
        </div>

        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method">GET</span>
                <span class="endpoint-path">/tasks/due</span>
            </div>
            <div class="endpoint-content">
                <p><strong>Description:</strong> Get tasks due within specified hours</p>
                <div class="parameter"><strong>hours:</strong> integer (optional, default: 24) - Number of hours to look ahead</div>
                <div class="code-block"># Get tasks due in next 48 hours
curl "{base_url}/tasks/due?hours=48"</div>
            </div>
        </div>

        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method">GET</span>
                <span class="endpoint-path">/tasks/export/csv</span>
            </div>
            <div class="endpoint-content">
                <p><strong>Description:</strong> Export all tasks as CSV file</p>
                <p><strong>Returns:</strong> CSV file download with filename 'tasks.csv'</p>
                <div class="code-block">curl {base_url}/tasks/export/csv -o tasks.csv</div>
            </div>
        </div>
    </div>

    <div id="models" class="section">
        <h2>DATA MODELS</h2>
        
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
                    <td><span class="badge">AUTO</span></td>
                </tr>
                <tr>
                    <td><code>title</code></td>
                    <td>string</td>
                    <td>Task title</td>
                    <td><span class="badge">YES</span></td>
                </tr>
                <tr>
                    <td><code>description</code></td>
                    <td>string</td>
                    <td>Task description</td>
                    <td><span class="badge">YES</span></td>
                </tr>
                <tr>
                    <td><code>priority</code></td>
                    <td>string</td>
                    <td>Priority level: low, medium, high</td>
                    <td><span class="badge">YES</span></td>
                </tr>
                <tr>
                    <td><code>status</code></td>
                    <td>string</td>
                    <td>Current status: TODO, IN_PROGRESS, COMPLETED</td>
                    <td><span class="badge">YES</span></td>
                </tr>
                <tr>
                    <td><code>due_date</code></td>
                    <td>string</td>
                    <td>ISO datetime when task is due</td>
                    <td><span class="badge">YES</span></td>
                </tr>
                <tr>
                    <td><code>created_at</code></td>
                    <td>string</td>
                    <td>ISO datetime when task was created</td>
                    <td><span class="badge">AUTO</span></td>
                </tr>
                <tr>
                    <td><code>tags</code></td>
                    <td>array</td>
                    <td>List of string tags</td>
                    <td><span class="badge">NO</span></td>
                </tr>
            </tbody>
        </table>
    </div>

    <div id="errors" class="section">
        <h2>ERROR RESPONSES</h2>
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
                    <td>CREATED</td>
                    <td>Resource created successfully</td>
                </tr>
                <tr>
                    <td>204</td>
                    <td>NO CONTENT</td>
                    <td>Resource deleted successfully</td>
                </tr>
                <tr>
                    <td>400</td>
                    <td>BAD REQUEST</td>
                    <td>Invalid input parameters or malformed request</td>
                </tr>
                <tr>
                    <td>404</td>
                    <td>NOT FOUND</td>
                    <td>Resource not found</td>
                </tr>
                <tr>
                    <td>500</td>
                    <td>INTERNAL SERVER ERROR</td>
                    <td>Server error occurred</td>
                </tr>
                <tr>
                    <td>503</td>
                    <td>SERVICE UNAVAILABLE</td>
                    <td>Database connection issues</td>
                </tr>
            </tbody>
        </table>
    </div>

    <div id="setup" class="section">
        <h2>ENVIRONMENT SETUP</h2>
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
        <h2>COMPLETE EXAMPLES</h2>
        
        <h3>Create and Manage a Task Workflow</h3>
        <div class="code-block"># 1. Create a new task
curl -X POST {base_url}/tasks \
  -H "Content-Type: application/json" \
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
curl -X PUT {base_url}/tasks/[TASK_ID] \
  -H "Content-Type: application/json" \
  -d '{{"status": "IN_PROGRESS"}}'

# 4. Mark task as completed
curl -X PUT {base_url}/tasks/[TASK_ID] \
  -H "Content-Type: application/json" \
  -d '{{"status": "COMPLETED"}}'

# 5. Export all tasks to CSV
curl {base_url}/tasks/export/csv -o my_tasks.csv</div>

        <h3>Filtering Examples</h3>
        <div class="code-block"># Get all completed tasks
curl "{base_url}/tasks?status=COMPLETED"

# Get high priority tasks that are not completed
curl "{base_url}/tasks?priority=high&status=TODO"

# Get tasks due in the next week
curl "{base_url}/tasks/due?hours=168"

# Get tasks due before a specific date
curl "{base_url}/tasks?due_date_before=2024-12-25T00:00:00"</div>
    </div>

    <div class="section">
        <p style="text-align: center; border-top: 1px solid #000; padding-top: 15px;">
            <strong>TASK TRACKER API DOCUMENTATION | VERSION 1.0.0</strong><br>
            Need help? Check the <a href="/health" style="color: #000; text-decoration: underline;">health endpoint</a> or <a href="/status" style="color: #000; text-decoration: underline;">status endpoint</a>
        </p>
    </div>
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