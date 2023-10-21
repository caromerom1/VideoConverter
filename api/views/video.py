from flask import Blueprint
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import VideoSchema
from models.models import Video

video_bp = Blueprint("video", __name__)


@video_bp.route("/", methods=["GET"])
@jwt_required()
def get_all_videos():
    user_id = get_jwt_identity()

    videos_tasks = Video().query.filter(Video.user_id == user_id).all()

    return jsonify(VideoSchema(many=True).dump(videos_tasks)), 200
