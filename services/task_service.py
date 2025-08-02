from dto.task_dto import TaskSchema
from repositories.task_repository import TaskRepository
from marshmallow import ValidationError
import csv
from io import StringIO
from datetime import datetime, timezone

class TaskService:
    def __init__(self, db):
        self.repository = TaskRepository(db)
        self.schema = TaskSchema()

    def create_task(self, data):
        if "tags" not in data:
            data["tags"] = []  # Default to empty list
        try:
            validated_data = self.schema.load(data)
            validated_data["created_at"] = datetime.now(timezone.utc)
            inserted_task = self.repository.create(validated_data)
            return self.schema.dump(inserted_task), 201
        except ValidationError as err:
            return {"error": err.messages}, 400

    def get_all_tasks(self, filters=None):
        tasks = self.repository.get_all(filters)
        return self.schema.dump(tasks, many=True), 200

    def get_task_by_id(self, task_id):
        task = self.repository.get_by_id(task_id)
        if task:
            return self.schema.dump(task), 200
        else:
            return {"error": "Task not found"}, 404

    def update_task(self, task_id, data):
        if "tags" not in data:
            data["tags"] = []  # Default to empty list
        try:
            update_data = self.schema.load(data, partial=True)
            updated_task = self.repository.update(task_id, update_data)
            if updated_task:
                return self.schema.dump(updated_task), 200
            else:
                return {"error": "Task not found"}, 404
        except ValidationError as err:
            return {"error": err.messages}, 400

    def delete_task(self, task_id):
        success = self.repository.delete(task_id)
        if success:
            return {}, 204
        else:
            return {"error": "Task not found"}, 404

    def get_due_tasks(self, hours=24):
        tasks = self.repository.get_due_tasks(hours)
        return self.schema.dump(tasks, many=True), 200

    def get_tasks_csv(self):
        tasks = self.repository.get_all()
        tasks_list = [self.schema.dump(task) for task in tasks]
        for task in tasks_list:
            task["tags"] = ",".join(task["tags"])
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=self.schema.fields.keys())
        writer.writeheader()
        writer.writerows(tasks_list)
        return output.getvalue()