import os

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from celery_instance import celery
from enums.ConversionStatus import ConversionStatus
from models import db, Video, VideoSchema

video_bp = Blueprint("video", __name__)


@video_bp.route("/", methods=["GET"])
@jwt_required()
def get_all_videos():
    request_data = request.json
    user_id = get_jwt_identity()
    order = request_data.get("order", None)
    max = request_data.get("max", None)
    videos_tasks = Video().query.filter(Video.user_id == user_id)

    if order:
        order_criteria = Video.id.desc() if order == '1' else Video.id.asc()

        videos_tasks = videos_tasks.order_by(order_criteria)

    if max:
        videos_tasks = videos_tasks.limit(max)

    query_result = videos_tasks.all()

    return jsonify(VideoSchema(many=True).dump(query_result)), 200


@video_bp.route("/", methods=["POST"])
@jwt_required()
def convert_video():
    file = request.files["video"]

    if not request.files.get("video") or not file.filename:
        return jsonify({"msg": "No video uploaded"}), 400

    conversion_extension = request.form.get("conversion_extension")

    if not conversion_extension:
        return jsonify({"msg": "No conversion extension provided"}), 400

    if conversion_extension[0] == ".":
        conversion_extension = conversion_extension[1:]

    allowed_extensions = ["mp4", "webm", "avi", "wmv", "mpeg"]

    if conversion_extension not in allowed_extensions:
        return (
            jsonify(
                {
                    "msg": f"Conversion extension not allowed ({conversion_extension}). Allowed extensions are: {', '.join(allowed_extensions)}"
                }
            ),
            400,
        )

    user_id = get_jwt_identity()

    user_uploaded_folder = f"{current_app.config['ORIGINALS_FOLDER']}/{user_id}"
    user_converted_folder = f"{current_app.config['CONVERTED_FOLDER']}/{user_id}"

    os.makedirs(user_uploaded_folder, exist_ok=True)
    os.makedirs(user_converted_folder, exist_ok=True)

    secured_filename = secure_filename(file.filename)

    base_filename = secured_filename.split(".")[0]

    original_file_location = f"{user_uploaded_folder}/{secured_filename}"

    file.save(original_file_location)

    converted_file_location = f"{user_converted_folder}/{base_filename}"

    video_task = Video(
        user_id=user_id,
        original_path=original_file_location,
        converted_path=converted_file_location,
        conversion_extension=conversion_extension,
    )

    db.session.add(video_task)
    db.session.commit()

    try:
        celery.send_task(
            "video_tasks.convert_video",
            args=[
                {
                    "paths": {
                        "original": original_file_location,
                        "converted": converted_file_location,
                    },
                    "extension": conversion_extension,
                },
                video_task.id,
            ],
        )

        return (
            jsonify(
                {
                    "message": "Converting video...",
                    "task_id": video_task.id,
                }
            ),
            200,
        )

    except Exception as e:
        video_task.status = ConversionStatus.FAILED
        db.session.commit()
        return jsonify({"message": str(e)}), 500
