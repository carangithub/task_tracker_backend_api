from flask import Flask
from pymongo import MongoClient
from controllers.task_controller import task_bp
from services.task_service import TaskService

app = Flask(__name__)
client = MongoClient("mongodb://localhost:27017/")
db = client["tasktracker"]
app.config["task_service"] = TaskService(db)
app.register_blueprint(task_bp)

if __name__ == "__main__":
    app.run(debug=False)