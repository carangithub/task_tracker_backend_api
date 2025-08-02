from marshmallow import Schema, fields, validate

class TaskSchema(Schema):
    id = fields.Str(dump_only=True)
    title = fields.Str(required=True)
    description = fields.Str(required=True)
    priority = fields.Str(required=True, validate=validate.OneOf(["low", "medium", "high"]))
    status = fields.Str(required=True, validate=validate.OneOf(["TODO", "IN_PROGRESS", "COMPLETED"]))
    due_date = fields.DateTime(required=True)
    created_at = fields.DateTime(dump_only=True)
    tags = fields.List(fields.Str())  # No missing parameter