from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta

class TaskRepository:
    def __init__(self, db):
        self.collection = db["tasks"]

    def create(self, task_data):
        result = self.collection.insert_one(task_data)
        inserted_task = self.collection.find_one({"_id": result.inserted_id})
        inserted_task["id"] = str(inserted_task["_id"])
        del inserted_task["_id"]
        return inserted_task

    def get_all(self, filters=None):
        query = {}
        if filters:
            if "priority" in filters:
                query["priority"] = filters["priority"]
            if "status" in filters:
                query["status"] = filters["status"]
            if "due_date_before" in filters:
                query["due_date"] = query.get("due_date", {})
                query["due_date"]["$lte"] = filters["due_date_before"]
            if "due_date_after" in filters:
                query["due_date"] = query.get("due_date", {})
                query["due_date"]["$gte"] = filters["due_date_after"]
        tasks = list(self.collection.find(query))
        for task in tasks:
            task["id"] = str(task["_id"])
            del task["_id"]
        return tasks

    def get_by_id(self, task_id):
        try:
            task = self.collection.find_one({"_id": ObjectId(task_id)})
            if task:
                task["id"] = str(task["_id"])
                del task["_id"]
            return task
        except:
            return None

    def update(self, task_id, update_data):
        try:
            result = self.collection.update_one({"_id": ObjectId(task_id)}, {"$set": update_data})
            if result.modified_count > 0:
                updated_task = self.get_by_id(task_id)
                return updated_task
            else:
                return None
        except:
            return None

    def delete(self, task_id):
        try:
            result = self.collection.delete_one({"_id": ObjectId(task_id)})
            return result.deleted_count > 0
        except:
            return False

    def get_due_tasks(self, hours=24):
        now = datetime.utcnow()
        due_time = now + timedelta(hours=hours)
        query = {
            "due_date": {"$gte": now, "$lte": due_time}
        }
        tasks = list(self.collection.find(query))
        for task in tasks:
            task["id"] = str(task["_id"])
            del task["_id"]
        return tasks