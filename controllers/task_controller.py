from flask import Blueprint, request, jsonify, make_response, current_app
from bson.objectid import InvalidId
from dateutil import parser

task_bp = Blueprint("task", __name__)

@task_bp.route("/tasks", methods=["POST"])
def create_task():
    task_service = current_app.config["task_service"]
    data = request.get_json()
    result, status_code = task_service.create_task(data)
    return jsonify(result), status_code

@task_bp.route("/tasks", methods=["GET"])
def get_tasks():
    task_service = current_app.config["task_service"]
    filters = {}
    if "priority" in request.args:
        filters["priority"] = request.args["priority"]
    if "status" in request.args:
        filters["status"] = request.args["status"]
    if "due_date_before" in request.args:
        try:
            filters["due_date_before"] = parser.parse(request.args["due_date_before"])
        except ValueError:
            return jsonify({"error": "Invalid due_date_before format"}), 400
    if "due_date_after" in request.args:
        try:
            filters["due_date_after"] = parser.parse(request.args["due_date_after"])
        except ValueError:
            return jsonify({"error": "Invalid due_date_after format"}), 400
    result, status_code = task_service.get_all_tasks(filters)
    return jsonify(result), status_code

@task_bp.route("/tasks/<task_id>", methods=["GET"])
def get_task(task_id):
    task_service = current_app.config["task_service"]
    try:
        result, status_code = task_service.get_task_by_id(task_id)
        return jsonify(result), status_code
    except InvalidId:
        return jsonify({"error": "Invalid task ID"}), 400

@task_bp.route("/tasks/<task_id>", methods=["PUT"])
def update_task(task_id):
    task_service = current_app.config["task_service"]
    data = request.get_json()
    try:
        result, status_code = task_service.update_task(task_id, data)
        return jsonify(result), status_code
    except InvalidId:
        return jsonify({"error": "Invalid task ID"}), 400

@task_bp.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    task_service = current_app.config["task_service"]
    try:
        result, status_code = task_service.delete_task(task_id)
        if status_code == 204:
            return "", 204
        else:
            return jsonify(result), status_code
    except InvalidId:
        return jsonify({"error": "Invalid task ID"}), 400

@task_bp.route("/tasks/due", methods=["GET"])
def get_due_tasks():
    task_service = current_app.config["task_service"]
    hours = request.args.get("hours", 24, type=int)
    result, status_code = task_service.get_due_tasks(hours)
    return jsonify(result), status_code

@task_bp.route("/tasks/export/csv", methods=["GET"])
def export_tasks_csv():
    task_service = current_app.config["task_service"]
    csv_content = task_service.get_tasks_csv()
    response = make_response(csv_content)
    response.headers["Content-Disposition"] = "attachment; filename=tasks.csv"
    response.headers["Content-Type"] = "text/csv"
    return response