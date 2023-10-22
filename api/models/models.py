from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from enums.ConversionStatus import ConversionStatus

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20))
    email = db.Column(db.String(40))
    password = db.Column(db.String(50))


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        include_relationships = True
        load_instance = True


class Video(db.Model):
    conversion_extension = db.Column(db.String(255), nullable=False)
    conversion_task_id = db.Column(db.String(255), unique=True)
    converted_path = db.Column(db.String(255), nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    original_path = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Enum(ConversionStatus), default=ConversionStatus.PENDING)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


class VideoSchema(SQLAlchemyAutoSchema):
    status = fields.Method("serialize_status")
    class Meta:
        model = Video
        fields = ("id", "conversion_extension", "status")
        include_relationships = True
        load_instance = True

    def serialize_status(self, obj):
        return obj.status.value
