from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from datetime import datetime

from enums.ConversionStatus import ConversionStatus

from . import db


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
    class Meta:
        model = Video
        fields = ("id", "conversion_extension", "status")
        include_relationships = True
        load_instance = True
