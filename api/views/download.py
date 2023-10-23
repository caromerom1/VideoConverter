import os

from flask import Blueprint, jsonify, request, send_from_directory
from flask_jwt_extended import get_jwt_identity, jwt_required
from enums.ConversionStatus import ConversionStatus

from models import Video


download_bp = Blueprint("download", __name__)


@download_bp.route("/video/<task_id>", methods=["GET"])
@jwt_required()
def download_video(task_id):
    if not task_id:
        return jsonify({"message": "No task_id provided"}), 400

    request_data = request.args

    converted = request_data.get(
        "converted", default=False, type=lambda val: val.lower() == "true"
    )
    filename = request_data.get("filename", None)

    if not filename:
        return jsonify({"message": "No filename provided"}), 400

    user_id = get_jwt_identity()

    video_task = (
        Video().query.filter(Video.user_id == user_id, Video.id == task_id).first()
    )

    if not video_task:
        return jsonify({"message": "Video not found"}), 404

    if video_task.status != ConversionStatus.SUCCESS:
        return jsonify({"message": "Video not ready for download"}), 400

    filepath = video_task.converted_path if converted else video_task.original_path

    directory = os.path.dirname(filepath)

    try:
        return send_from_directory(directory, filename, as_attachment=True)
    except:
        return jsonify({"message": "Video not found"}), 404
